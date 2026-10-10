using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Nodes;
using TurboJev;

internal static class Examples
{
    private static readonly JsonSerializerOptions Pretty = new() { WriteIndented = true };
    private static string Data(string example, string file) => Path.Combine(AppContext.BaseDirectory, "data", example, file);

    public static JsonNode? CreateRequest(Options options, JsonObject report)
    {
        if (options.Example == "fair-die") return null;
        if (options.Example is "structured" or "hierarchical" or "discover-categories" or "dice" or "limits")
        {
            return JsonNode.Parse(File.ReadAllText(Data("recipes", $"{options.Example}.json")));
        }
        if (options.Example == "ticket") return JsonSerializer.SerializeToNode(new
        {
            state = new { ticket = "My package arrived broken. Please send a replacement." },
            questions = new Dictionary<string, object>
            {
                ["team"] = new
                {
                    type = "choice",
                    instructions = "Which team should handle this ticket?",
                    criteria = new Dictionary<string, string>
                    {
                        ["billing"] = "Payments and refunds",
                        ["technical"] = "Bugs and outages",
                        ["shipping"] = "Delivery problems"
                    }
                },
                ["urgency"] = new { type = "score", instructions = "How urgent is this ticket?", criteria = new[] { "Can wait", "This week", "Today" } },
                ["wantsRefund"] = new { type = "noul", instructions = "Does the customer ask for a refund?" },
            },
        });
        if (options.Example == "fields") return JsonNode.Parse("""
            {
              "context": "There are seven overdue invoices. Their total is 324.50 GBP. No payment reference is provided.",
              "thinking": false,
              "questions": {
                "count": {"type":"integer", "instructions":"How many invoices are overdue?"},
                "total": {"type":"number", "instructions":"What is the total in GBP?"},
                "overdue": {"type":"boolean", "instructions":"Are there overdue invoices?", "return_probabilities":true},
                "reference": {"type":["string","null"], "instructions":"Return the payment reference, or null if absent."},
                "reminder": {"type":"string", "when":{"overdue":true}, "depends_on":["total"], "instructions":"Write one short payment reminder including the total."},
                "large_account_note": {"type":"string", "when":{"count":{"gt":10}}, "instructions":"Write a short note about the high invoice count."}
              }
            }
            """)!.WithLimits(options.MaxTokens);

        var image = Path.GetFullPath(options.Image ?? Data("receipt", "receipt.jpg"));
        if (!File.Exists(image) || new FileInfo(image).Length is <= 0 or > 24 * 1024 * 1024)
            throw new ArgumentException("Provide a nonempty receipt image of at most 24 MiB.");
        var questions = JsonNode.Parse(File.ReadAllText(Data(options.Example, "questions.json")))!.AsObject();
        if (options.Fields is not null)
        {
            var names = options.Fields.Split(',').Select(x => x.Trim()).ToHashSet(StringComparer.Ordinal);
            foreach (var name in names)
                if (!questions.ContainsKey(name)) throw new ArgumentException($"Unknown receipt field: {name}.");
            // Include dependency closure while preserving the original field order.
            var changed = true;
            while (changed)
            {
                changed = false;
                foreach (var name in names.ToArray())
                    if (questions[name]!["depends_on"] is JsonArray dependencies)
                        foreach (var dependency in dependencies) changed |= names.Add(dependency!.GetValue<string>());
            }
            foreach (var name in questions.Select(pair => pair.Key).ToArray())
                if (!names.Contains(name)) questions.Remove(name);
        }
        report["fields"] = new JsonArray(questions.Select(pair => (JsonNode?)JsonValue.Create(pair.Key)).ToArray());
        report["subset"] = options.Fields is not null;
        report["max_tokens"] = options.MaxTokens;
        report["thinking"] = false;
        report["image"] = image;
        report["image_sha256"] = Models.Hash(image);
        return new JsonObject
        {
            ["context"] = new JsonObject
            {
                ["contract"] = "turbojev.media.v1",
                ["modality"] = "image",
                ["text"] = "Read the attached photo of a restaurant receipt.",
                ["base64"] = Convert.ToBase64String(File.ReadAllBytes(image)),
            },
            ["questions"] = questions,
            ["thinking"] = false,
            ["text_max_tokens"] = options.MaxTokens,
            ["numeric_max_tokens"] = options.MaxTokens,
        };
    }

    private static JsonNode WithLimits(this JsonNode request, int tokens)
    {
        request["text_max_tokens"] = tokens;
        request["numeric_max_tokens"] = tokens;
        return request;
    }

    public static async Task FairDieAsync(TurboJevEngine engine, Options options, JsonObject runs)
    {
        var labels = new[] { "one", "two", "three", "four", "five", "six" };
        object[] budgets = options.AllPermutations ? [1, "auto", 8, "all"] : [1, "auto", 8];
        foreach (var budget in budgets)
        {
            Console.WriteLine($"Evaluating permutation budget {budget}…");
            var request = new
            {
                context = "A single roll of a fair die.",
                seed = 42,
                mode = "argmax",
                temperature = 1,
                questions = new Dictionary<string, object>
                {
                    ["roll"] = new Dice(budget).ToSchema(),
                },
            };
            var timer = Stopwatch.StartNew();
            var response = JsonNode.Parse(await engine.GenerateJsonAsync(JsonSerializer.Serialize(request)))!;
            var seconds = timer.Elapsed.TotalSeconds;
            var probabilities = response["result"]!["roll"]!["probabilities"]!.AsObject();
            var values = probabilities.Select(pair => pair.Value!.GetValue<double>()).ToArray();
            if (!labels.ToHashSet().SetEquals(probabilities.Select(pair => pair.Key)) || values.Any(p => !double.IsFinite(p) || p < 0 || p > 1) || Math.Abs(values.Sum() - 1) > 1e-9)
                throw new InvalidDataException("Invalid model distribution.");
            // Compare only after inference. Do not replace model scores with uniform values.
            double? kl = values.All(p => p > 0) ? values.Sum(p => Math.Log((1d / 6) / p) / 6) : null;
            var run = new JsonObject { ["response"] = response, ["seconds"] = seconds, ["kl_uniform_to_prediction"] = kl };
            runs[budget.ToString()!] = run;
            Console.WriteLine(run.ToJsonString(Pretty));
        }
    }

    public static void CompareLabels(Options options, JsonObject report, JsonObject actual)
    {
        var useLabels = options.ReferenceLabels || options.Example == "receipt" && report["image_sha256"]!.GetValue<string>() == Models.Hash(Data("receipt", "receipt.jpg"));
        var expected = new JsonObject();
        var matches = new JsonObject();
        if (useLabels)
        {
            var reference = JsonNode.Parse(File.ReadAllText(Data(options.Example, "expected.json")))!.AsObject();
            foreach (var field in report["fields"]!.AsArray())
            {
                var name = field!.GetValue<string>();
                if (!reference.TryGetPropertyValue(name, out var value)) continue;
                expected[name] = value!.DeepClone();
                matches[name] = Matches(actual[name], value);
            }
        }
        report["expected"] = expected;
        report["matches"] = matches;
        if (matches.Count > 0) Console.WriteLine($"Reference labels: {matches.Count(pair => pair.Value!.GetValue<bool>())}/{matches.Count} fields match.");
    }

    private static bool Matches(JsonNode? actual, JsonNode expected)
    {
        if (actual is null || actual.GetValueKind() != expected.GetValueKind()) return false;
        if (expected.GetValueKind() == JsonValueKind.Number)
        {
            var wanted = expected.GetValue<double>();
            return Math.Abs(actual.GetValue<double>() - wanted) <= Math.Max(1e-6, Math.Abs(wanted) * 1e-6);
        }
        return JsonNode.DeepEquals(actual, expected);
    }
}

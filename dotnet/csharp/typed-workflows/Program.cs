using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using TurboJev;

var jsonOptions = new JsonSerializerOptions { WriteIndented = true };
if (args.Contains("--help") || args.Contains("-h"))
{
    Console.WriteLine(Options.Help);
    return 0;
}
Options options;
try { options = Options.Parse(args); }
catch (ArgumentException error)
{
    Console.Error.WriteLine($"{error.Message}\n\n{Options.Help}");
    return 2;
}
var report = new JsonObject
{
    ["example"] = options.Example,
    ["turbojev"] = typeof(TurboJevEngine).Assembly.GetName().Version?.ToString(),
    ["package_version"] = "0.33.1",
    ["platform"] = RuntimeInformation.OSDescription,
    ["architecture"] = RuntimeInformation.ProcessArchitecture.ToString(),
    ["device"] = options.Device,
};
try
{
    var request = Examples.CreateRequest(options, report);
    var model = await Models.ResolveAsync(options.Model, options.IsVision);
    var projector = options.IsVision ? await Models.ResolveProjectorAsync(options.Projector) : null;
    report["model"] = model;
    report["model_sha256"] = Models.Hash(model);
    if (projector is not null)
    {
        report["mmproj"] = projector;
        report["mmproj_sha256"] = Models.Hash(projector);
    }
    Console.WriteLine($"TurboJev 0.33.1 | {options.Example} | {Path.GetFileName(model)} | {options.Device}");
    var timer = Stopwatch.StartNew();
    await using var engine = await TurboJevEngine.LoadAsync(new
    {
        model,
        mmproj = projector,
        device = options.Device,
        nCtx = 8192,
        nSeqMax = 1,
        nThreads = 4,
        nThreadsBatch = 4,
        // "none": one pass. "balanced": canonical probability mean; "cyclic": rotation logit mean.
        // Both corrected modes cost extra inference and preserve ordered score scales.
        // generate enums use their own permutations budget; see fair-die.
        execution = new { orderRobustness = "none" },
    });
    report["load_seconds"] = timer.Elapsed.TotalSeconds;
    if (options.Example == "fair-die")
    {
        report["seed"] = 42;
        report["ground_truth"] = JsonSerializer.SerializeToNode(new[] { "one", "two", "three", "four", "five", "six" }.ToDictionary(label => label, _ => 1d / 6));
        var runs = new JsonObject();
        report["runs"] = runs;
        await Examples.FairDieAsync(engine, options, runs);
    }
    else
    {
        Console.WriteLine(options.IsVision
            ? $"Reading {report["fields"]!.AsArray().Count} fields; image inference may take several minutes."
            : "Evaluating…");
        timer.Restart();
        var response = JsonNode.Parse(options.Example == "ticket"
            ? await engine.EvaluateJsonAsync(request!.ToJsonString())
            : await engine.GenerateJsonAsync(request!.ToJsonString()))!;
        report["evaluation_seconds"] = timer.Elapsed.TotalSeconds;
        report["response"] = response;
        if (options.IsVision) Examples.CompareLabels(options, report, response["result"]!.AsObject());
        Console.WriteLine(response.ToJsonString(jsonOptions));
        Console.WriteLine($"Load: {report["load_seconds"]!.GetValue<double>():F3}s | Evaluation: {timer.Elapsed.TotalSeconds:F3}s");
    }
    report["ok"] = true;
    report["error"] = null;
}
catch (Exception error)
{
    report["ok"] = false;
    report["error"] = error.Message;
    Console.Error.WriteLine(error.Message);
}
var output = Path.GetFullPath(options.Output ?? $"result-{options.Example}.json");
Directory.CreateDirectory(Path.GetDirectoryName(output)!);
await File.WriteAllTextAsync(output, report.ToJsonString(jsonOptions) + "\n");
Console.WriteLine($"Report saved: {output}");
return report["ok"]!.GetValue<bool>() ? 0 : 2;

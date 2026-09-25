using System.Diagnostics;
using System.Net.Http;
using System.Text.Json;
using TurboJev;

var model = Environment.GetEnvironmentVariable("TURBOJEV_MODEL");
if (string.IsNullOrWhiteSpace(model)) {
    var cache = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".cache", "turbojev", "Qwen3-0.6B-Q4_K_M.gguf");
    Directory.CreateDirectory(Path.GetDirectoryName(cache)!);
    if (!File.Exists(cache)) {
        Console.WriteLine("Downloading Qwen3 0.6B Q4_K_M (~0.48 GB)...");
        using var http = new HttpClient();
        using var downloadResponse = await http.GetAsync("https://huggingface.co/bartowski/Qwen_Qwen3-0.6B-GGUF/resolve/main/Qwen_Qwen3-0.6B-Q4_K_M.gguf?download=true", HttpCompletionOption.ResponseHeadersRead);
        downloadResponse.EnsureSuccessStatusCode();
        var temporary = cache + ".part";
        try {
            await using var source = await downloadResponse.Content.ReadAsStreamAsync();
            await using var target = File.Create(temporary);
            var total = downloadResponse.Content.Headers.ContentLength ?? 0;
            var buffer = new byte[1024 * 1024];
            long received = 0;
            int count;
            while ((count = await source.ReadAsync(buffer)) > 0) {
                await target.WriteAsync(buffer.AsMemory(0, count));
                received += count;
                if (total > 0) {
                    var ratio = Math.Min(1d, (double)received / total);
                    const int width = 28;
                    var filled = (int)Math.Round(ratio * width);
                    Console.Write($"\rQwen3 0.6B [{new string('█', filled)}{new string('─', width - filled)}] {ratio:P1}  {received / 1048576d:F0} / {total / 1048576d:F0} MB");
                } else Console.Write($"\rDownloading Qwen3 0.6B: {received / 1048576d:F0} MB");
            }
            Console.WriteLine();
            File.Move(temporary, cache, overwrite: true);
        } catch {
            if (File.Exists(temporary)) File.Delete(temporary);
            Console.WriteLine();
            throw;
        }
    }
    model = cache;
}
await using var engine = await TurboJevEngine.LoadAsync(new { model, nGpuLayers = 0, nThreads = 4 });
var request = new {
    state = new { ticket = "My package arrived broken. Please send a replacement." },
    questions = new Dictionary<string, object> {
        ["team"] = new {
            type = "choice",
            instructions = "Which team should handle this ticket?",
            criteria = new Dictionary<string, string> {
                ["billing"] = "Payments and refunds",
                ["technical"] = "Bugs and outages",
                ["shipping"] = "Delivery problems",
            },
        },
        ["urgency"] = new {
            type = "score",
            instructions = "How urgent is this ticket?",
            criteria = new[] { "Can wait", "This week", "Today" },
        },
        ["wantsRefund"] = new {
            type = "noul",
            instructions = "Does the customer ask for a refund?",
        },
    },
};
var timer = Stopwatch.StartNew();
var response = await engine.EvaluateJsonAsync(JsonSerializer.Serialize(request));
Console.WriteLine(JsonSerializer.Serialize(JsonDocument.Parse(response), new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine($"Elapsed: {timer.Elapsed.TotalSeconds:F2} s");

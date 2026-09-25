using System.Diagnostics;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text.Json;
using TurboJev;

const long expectedModelBytes = 484_220_320;
const string expectedModelSha256 = "9acfc1e001311f34b4252001b626f2e466d592a42065f66571bff3790d4e1b14";
const string modelUrl = "https://huggingface.co/bartowski/Qwen_Qwen3-0.6B-GGUF/resolve/60b85c0e3d8fe0f6474f406922a26d12aca4550d/Qwen_Qwen3-0.6B-Q4_K_M.gguf?download=true";

static bool IsValidModel(string path, long expectedBytes, string expectedSha256)
{
    if (!File.Exists(path) || new FileInfo(path).Length != expectedBytes) return false;
    using var stream = File.OpenRead(path);
    return Convert.ToHexString(SHA256.HashData(stream)).Equals(expectedSha256, StringComparison.OrdinalIgnoreCase);
}

var model = Environment.GetEnvironmentVariable("TURBOJEV_MODEL");
if (string.IsNullOrWhiteSpace(model)) {
    var cache = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".cache", "turbojev", "Qwen3-0.6B-Q4_K_M.gguf");
    Directory.CreateDirectory(Path.GetDirectoryName(cache)!);
    if (!IsValidModel(cache, expectedModelBytes, expectedModelSha256)) {
        if (File.Exists(cache)) Console.WriteLine("Cached model is incomplete or invalid; downloading a verified copy.");
        Console.WriteLine("Downloading Qwen3 0.6B Q4_K_M (~0.48 GB)...");
        using var http = new HttpClient { Timeout = Timeout.InfiniteTimeSpan };
        using var downloadResponse = await http.GetAsync(modelUrl, HttpCompletionOption.ResponseHeadersRead);
        downloadResponse.EnsureSuccessStatusCode();
        if (downloadResponse.Content.Headers.ContentLength is long contentLength && contentLength != expectedModelBytes)
            throw new InvalidDataException($"Unexpected model size: server reports {contentLength} bytes; expected {expectedModelBytes}.");
        var temporary = cache + ".part";
        try {
            await using var source = await downloadResponse.Content.ReadAsStreamAsync();
            await using var target = File.Create(temporary);
            var total = downloadResponse.Content.Headers.ContentLength ?? 0;
            var buffer = new byte[1024 * 1024];
            long received = 0;
            var lastReportedPercent = -1;
            int count;
            while ((count = await source.ReadAsync(buffer)) > 0) {
                await target.WriteAsync(buffer.AsMemory(0, count));
                received += count;
                if (total > 0) {
                    var ratio = Math.Min(1d, (double)received / total);
                    var percent = (int)(ratio * 100);
                    if (percent != lastReportedPercent) {
                        const int width = 28;
                        var filled = (int)Math.Round(ratio * width);
                        Console.Write($"\rQwen3 0.6B [{new string('█', filled)}{new string('─', width - filled)}] {ratio:P0}  {received / 1048576d:F0} / {total / 1048576d:F0} MB");
                        lastReportedPercent = percent;
                    }
                } else Console.Write($"\rDownloading Qwen3 0.6B: {received / 1048576d:F0} MB");
            }
            await target.DisposeAsync();
            Console.WriteLine();
            if (received != expectedModelBytes)
                throw new InvalidDataException($"Model download was incomplete: received {received} of {expectedModelBytes} bytes.");
            await using (var verificationStream = File.OpenRead(temporary)) {
                var sha256 = Convert.ToHexString(await SHA256.HashDataAsync(verificationStream));
                if (!sha256.Equals(expectedModelSha256, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException($"Model SHA-256 mismatch: received {sha256}.");
            }
            File.Move(temporary, cache, overwrite: true);
        } catch {
            if (File.Exists(temporary)) File.Delete(temporary);
            Console.WriteLine();
            throw;
        }
    }
    model = cache;
}
await using var engine = await TurboJevEngine.LoadAsync(new {
    model,
    nGpuLayers = 0,
    nThreads = 4,
    execution = new { orderRobustness = "none" },
});
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

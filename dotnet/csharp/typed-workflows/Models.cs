using System.Diagnostics;
using System.Security.Cryptography;

internal static class Models
{
    // Default text model: QJev3.5 0.8B v19c, standalone Q8_0 (811,843,104 bytes).
    // Decision-trained weights; not a general extraction, reasoning or vision model.
    // TurboJev uses its normal prompt/scoring path; upstream benchmark claims do not transfer.
    // Alternatives (download locally and pass --model PATH; no automatic fallback):
    // Jev-Style 2B v2 (letter scoring; requires its trained prompt)
    // https://huggingface.co/chaoliangUNSW/Jev-Style-Qwen3.5-2B-Decision-v2-GGUF
    // Jev-Style 0.8B v3 (requires a per-option verdict scorer)
    // https://huggingface.co/chaoliangUNSW/Jev-Style-0.8B-Decision-v3-GGUF
    // Jev-Style 2B v3 (requires block attention and a verdict scorer)
    // https://huggingface.co/chaoliangUNSW/Jev-Style-2B-Decision-v3-GGUF
    private const string TextModelName = "qjev35-v19c-q8_0.gguf";
    private const string TextModelUrl = "https://huggingface.co/ZY-Lee4/QJev3.5-0.8B-GGUF/resolve/008c7c7a5c35007b8ba6b06afba50f882f000667/qjev35-v19c-q8_0.gguf";
    private const long TextModelBytes = 811_843_104;
    private const string TextModelSha256 = "7a5a50953df2fb866a2f39bc4ac8906084cac4e3a5fa8f04adc519058ceedf87";

    private const string VisionRoot = "https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/resolve/f6d5376be1edb4d416d56da11e5397a961aca8ae/";
    private static readonly string Cache = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".cache", "turbojev");
    public static Task<string> ResolveAsync(string? path, bool vision)
    {
        path ??= vision ? null : Environment.GetEnvironmentVariable("TURBOJEV_MODEL");
        if (!string.IsNullOrWhiteSpace(path)) return Task.FromResult(ValidateCustom(path));
        return vision
            ? DownloadAsync("Qwen3.5-2B-Q4_K_M.gguf", VisionRoot + "Qwen3.5-2B-Q4_K_M.gguf", 1_280_835_840)
            : DownloadAsync(TextModelName, TextModelUrl, TextModelBytes, TextModelSha256);
    }
    public static Task<string> ResolveProjectorAsync(string? path) => path is not null
        ? Task.FromResult(ValidateCustom(path))
        : DownloadAsync("Qwen3.5-2B-mmproj-F16.gguf", VisionRoot + "mmproj-F16.gguf", 668_227_264);
    public static string Hash(string path)
    {
        using var stream = File.OpenRead(path);
        return Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
    }
    private static string ValidateCustom(string path)
    {
        path = Path.GetFullPath(path);
        if (!IsGguf(path)) throw new InvalidDataException($"Not a readable GGUF file: {path}");
        return path;
    }
    private static bool IsGguf(string path)
    {
        if (!File.Exists(path) || new FileInfo(path).Length < 4) return false;
        using var stream = File.OpenRead(path);
        Span<byte> magic = stackalloc byte[4];
        return stream.Read(magic) == 4 && magic.SequenceEqual("GGUF"u8);
    }
    private static bool IsValid(string path, long bytes, string? sha256) => IsGguf(path) && new FileInfo(path).Length == bytes && (sha256 is null || Hash(path) == sha256);
    private static async Task<string> DownloadAsync(string name, string url, long bytes, string? sha256 = null)
    {
        Directory.CreateDirectory(Cache);
        var path = Path.Combine(Cache, name);
        if (IsValid(path, bytes, sha256)) { Console.WriteLine($"Model cache hit: {name}"); return path; }
        var temporary = path + ".part";
        Console.WriteLine($"Downloading {name}…");
        using var http = new HttpClient { Timeout = Timeout.InfiniteTimeSpan };
        try
        {
            using var response = await http.GetAsync(url, HttpCompletionOption.ResponseHeadersRead);
            response.EnsureSuccessStatusCode();
            if (response.Content.Headers.ContentLength is long length && length != bytes) throw new InvalidDataException($"Unexpected size: {length}; expected {bytes} bytes.");
            await using (var source = await response.Content.ReadAsStreamAsync())
            await using (var target = File.Create(temporary))
            {
                var timer = Stopwatch.StartNew();
                var buffer = new byte[1024 * 1024];
                long received = 0;
                var lastUpdate = -1d;
                int count;
                while ((count = await source.ReadAsync(buffer)) > 0)
                {
                    await target.WriteAsync(buffer.AsMemory(0, count));
                    received += count;
                    if (received > bytes) throw new InvalidDataException("Download exceeds the expected file size.");
                    if (timer.Elapsed.TotalSeconds - lastUpdate < 0.2 && received != bytes) continue;
                    lastUpdate = timer.Elapsed.TotalSeconds;
                    var ratio = (double)received / bytes;
                    var filled = (int)(ratio * 28);
                    var speed = received / Math.Max(timer.Elapsed.TotalSeconds, 0.001);
                    Console.Write($"\r[{new string('█', filled)}{new string('─', 28 - filled)}] {ratio:P1}  {received / 1048576d:F1}/{bytes / 1048576d:F1} MiB  {speed / 1048576:F1} MiB/s  ETA {(bytes - received) / speed:F0}s   ");
                }
            }
            Console.WriteLine();
            if (!IsValid(temporary, bytes, sha256)) throw new InvalidDataException("Incomplete or invalid GGUF download.");
            File.Move(temporary, path, overwrite: true);
            return path;
        }
        catch
        {
            if (File.Exists(temporary)) File.Delete(temporary);
            Console.WriteLine();
            throw;
        }
    }
}

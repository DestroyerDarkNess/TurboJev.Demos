internal sealed record Options
{
    public string Example { get; init; } = "ticket";
    public string Device { get; init; } = "cpu";
    public string? Model { get; init; }
    public string? Projector { get; init; }
    public string? Image { get; init; }
    public string? Fields { get; init; }
    public string? Output { get; init; }
    public int MaxTokens { get; init; } = 64;
    public bool ReferenceLabels { get; init; }
    public bool AllPermutations { get; init; }
    public bool IsVision => Example is "receipt" or "receipt-us";
    public const string Help = """
        Usage: dotnet run -c Release -- [ticket|fields|fair-die|receipt|receipt-us] [options]
          --device cpu|gpu     CPU by default; GPU errors do not fall back to CPU
          --model PATH         Compatible GGUF (or TURBOJEV_MODEL for text)
          --mmproj PATH        Matching vision projector; requires --model
          --image PATH         Receipt photo; required for receipt-us
          --fields a,b         Receipt subset; includes dependencies automatically
          --max-tokens N       Output tokens per generated field, default 64
          --reference-labels   Compare your image with the original receipt's labels
          --all-permutations   Fair die: also evaluate 720 orderings (slow)
          --output PATH        JSON report (default result-<example>.json)
          --help               Show commands
        """;
    public static Options Parse(string[] args)
    {
        var result = new Options();
        var position = 0;
        if (args.Length > 0 && !args[0].StartsWith('-')) result = result with { Example = args[position++] };
        while (position < args.Length)
        {
            var name = args[position++];
            if (name == "--reference-labels") { result = result with { ReferenceLabels = true }; continue; }
            if (name == "--all-permutations") { result = result with { AllPermutations = true }; continue; }
            if (position == args.Length || args[position].StartsWith("--")) throw new ArgumentException($"Missing value for {name}.");
            var value = args[position++];
            result = name switch
            {
                "--device" => result with { Device = value },
                "--model" => result with { Model = value },
                "--mmproj" => result with { Projector = value },
                "--image" => result with { Image = value },
                "--fields" => result with { Fields = value },
                "--output" => result with { Output = value },
                "--max-tokens" when int.TryParse(value, out var count) && count is >= 1 and <= 32768 => result with { MaxTokens = count },
                _ => throw new ArgumentException($"Unknown option or invalid value: {name} {value}."),
            };
        }
        if (result.Example is not ("ticket" or "fields" or "fair-die" or "receipt" or "receipt-us")) throw new ArgumentException($"Unknown example: {result.Example}.");
        if (result.Device is not ("cpu" or "gpu")) throw new ArgumentException("Device must be cpu or gpu.");
        if (!result.IsVision && (result.Image is not null || result.Fields is not null || result.Projector is not null || result.ReferenceLabels)) throw new ArgumentException("Image, fields, projector and reference labels are receipt options.");
        if (result.AllPermutations && result.Example != "fair-die") throw new ArgumentException("--all-permutations is a fair-die option.");
        if (result.Example == "receipt-us" && result.Image is null) throw new ArgumentException("receipt-us requires --image PATH.");
        if (result.IsVision && (result.Model is null) != (result.Projector is null)) throw new ArgumentException("Custom vision models require both --model and --mmproj.");
        return result;
    }
}

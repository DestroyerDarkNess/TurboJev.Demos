fn main() {
    // crates.io currently provides TurboJev's portable core, not its GGUF runtime.
    // This keeps the demo honest: the typed request contract is shown here, while
    // real Qwen inference is available in the Node, Python, and .NET demos.
    let request = serde_json::json!({
        "state": { "ticket": "My package arrived broken. Please send a replacement." },
        "questions": {
            "team": {
                "type": "choice",
                "instructions": "Which team should handle this ticket?",
                "criteria": {
                    "billing": "Payments and refunds",
                    "technical": "Bugs and outages",
                    "shipping": "Delivery problems"
                }
            },
            "urgency": {
                "type": "score",
                "instructions": "How urgent is this ticket?",
                "criteria": ["Can wait", "This week", "Today"]
            },
            "wantsRefund": {
                "type": "noul",
                "instructions": "Does the customer ask for a refund?"
            }
        }
    });
    println!("TurboJev typed-decision request (core crate, no model runtime):\n{request:#}");
}

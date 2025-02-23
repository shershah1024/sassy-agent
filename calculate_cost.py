def calculate_cost(input_tokens, output_tokens, model_name):
    model_costs = [{
        "model_name": "claude-3-5-sonnet-20240620",
        "input_token_cost": 3,
        "output_token_cost": 15
    }, {
        "model_name": "claude-3-haiku-20240307",
        "input_token_cost": .25,
        "output_token_cost": 1.25
    }, {
        "model_name": 'meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo',
        "input_token_cost": .88,
        "output_token_cost": .88
    }, {
        "model_name": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
        "input_token_cost": 5,
        "output_token_cost": 5
    }, {
        "model_name": "gpt-4o-mini",
        "input_token_cost": 0.15,
        "output_token_cost": 0.6
    }, {
        "model_name": "gpt-4o",
        "input_token_cost": 2.5,
        "output_token_cost": 10
    }, {
        "model_name": "gpt-4-o-3",
        "input_token_cost": 2.5,
        "output_token_cost": 10
    },
        {
            "model_name": "gpt-4-o-3",
            "input_token_cost": 2.5,
            "output_token_cost": 10
        }


    ]

    input_cost = 0
    output_cost = 0
    total_cost = 0

    # Find the specified model or use gpt-4o as default
    model = next((m for m in model_costs if m["model_name"] == model_name), None)
    if model is None:
        model = next(m for m in model_costs if m["model_name"] == "gpt-4o")
        print(f"Warning: Model '{model_name}' not found. Using 'gpt-4o' as default.")

    input_cost = (input_tokens / 1_000_000) * model["input_token_cost"]
    output_cost = (output_tokens / 1_000_000) * model["output_token_cost"]
    total_cost = input_cost + output_cost

    return input_cost, output_cost, total_cost

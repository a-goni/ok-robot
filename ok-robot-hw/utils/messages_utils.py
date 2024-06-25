from termcolor import colored

def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "tool": "magenta",
    }
    
    for message in messages:
        if message["role"] == "system":
            print(colored(f"System: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "user":
            for content in message["content"]:
                if content["type"] == "text":
                    print(colored(f"User:\n    Content: {content['text']}", role_to_color[message["role"]]))
                elif content["type"] == "image_url":
                    print(colored(f"    Image: [Image displayed on screen]\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant":
            print(colored(f"Assistant (Total tokens: {message['usage']['total_tokens']}):\n", role_to_color[message["role"]]))
            for content in message["content"]:
                if content["type"] == "text":
                    print(colored(f"{content['text']}\n", role_to_color[message["role"]]))
            if "tool_calls" in message and message["tool_calls"]:
                for tool_call in message["tool_calls"]:
                    print(colored(f"Tool Call:\n  Function Name: {tool_call['function']['name']}\n  Arguments: {tool_call['function']['arguments']}\n  Type: {tool_call['type']}\n", role_to_color["assistant"]))
        elif message["role"] == "tool":
            print(colored(f"Tool: {message['content']}\n", role_to_color[message["role"]]))

def add_system_message(messages):
    system_message = """
    You are an autonomous robot in a lab environment with a mobile base and a camera.       
    Your task is to to find and navigate to the miniature toy kitchen in the lab, avoiding bumping into anything.
    A good way to initially see the environment is to turn on the spot. Making small movements will also help to avoid obstacles.
    The toy kitchen is in the room/lab environment. You do not need to exit through the corridors.
    Succinctly describe what you want to do in one sentence and use the provided function calls to execute navigation. 
    Once you find the toy kitchen, tell me you have made it, and perform no further actions.
    """

    new_message = [{
        "role": "system", 
        "content": system_message
    }]
    pretty_print_conversation(new_message)
    messages.append(new_message[0])
    return messages

def add_image_message(encoded_image, messages):
    new_message = [{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Image has a FOV (HxW) of 69°x42°."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{encoded_image}"
                            }
                    }
                ]}]
    pretty_print_conversation(new_message)
    messages.append(new_message[0])
    return messages

def add_response_message(response, messages):
    # TODO
    # - Add handling where content is none.
    # - Add handling for multiple tool calls.
    tool_calls = getattr(response.choices[0].message, 'tool_calls', None)
    if tool_calls:
        new_message = [{
                "chat_completion_id": response.id,
                "created": response.created,
                "model": response.model,
                "system_fingerprint": response.system_fingerprint,
                "usage": {
                    "completion_tokens": response.usage.completion_tokens,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "role": response.choices[0].message.role,
                "content": [
                    {
                        "type": "text",
                        "text": response.choices[0].message.content
                    }
                ],
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        },
                        "type": tool_call.type
                    } for tool_call in response.choices[0].message.tool_calls
                ]
            }]
    else:
        new_message = [{
                "chat_completion_id": response.id,
                "created": response.created,
                "model": response.model,
                "system_fingerprint": response.system_fingerprint,
                "usage": {
                    "completion_tokens": response.usage.completion_tokens,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "role": response.choices[0].message.role,
                "content": [
                    {
                        "type": "text",
                        "text": response.choices[0].message.content
                    }
                ]
            }]   
    pretty_print_conversation(new_message)
    messages.append(new_message[0])
    return messages

def add_tool_message(tool_call, function_name, messages):
    new_message = [{
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": "Performed action.",
                    }]
    pretty_print_conversation(new_message)
    messages.append(new_message[0])
    return messages
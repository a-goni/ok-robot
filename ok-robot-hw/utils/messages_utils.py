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
                    print(colored(f"{content['text']}", role_to_color[message["role"]]))
            if "tool_calls" in message and message["tool_calls"]:
                for tool_call in message["tool_calls"]:
                    print(colored(f"Tool Call:\n  Function Name: {tool_call['function']['name']}\n  Arguments: {tool_call['function']['arguments']}\n  Type: {tool_call['type']}\n", role_to_color["assistant"]))
        elif message["role"] == "tool":
            print(colored(f"Tool: {message['content']}\n", role_to_color[message["role"]]))

def modify_last_entry(data):
    # Access the last entry in the data list
    last_entry = data[-1]
    
    # Iterate through content in the last entry
    for content in last_entry['content']:
        # Check if the content type is 'image_url'
        if content['type'] == 'image_url':
            # Replace the image data with a text notification
            content['type'] = 'text'
            content['text'] = 'encoded image removed.'
            # Remove the image_url key
            del content['image_url']
    
    return data

def add_system_message(messages):
    system_message = """
    You are an autonomous robot with a mobile base and a camera with an image FOV (HxW) of 69°x42°.       
    Your task is to find and navigate to the toy kitchen in the lab, avoiding obstacles.
    Make small movements (0.5 to 1m) to help avoid collisions with obstacles. Turning on the spot can help to adjust course. Avoid being closer than 1m to any object.
    The toy kitchen is in the immediate area. You do not need to exit the room, or lab area. 
    Provide a text response and use an in built function/tool call.

    Text Response Format:
        Latest Image: [provide one sentence to describe the image and any relevant information.]
        Map: [describe where you have been, using previous tool calls]
        Plan: [describe the plan to find the kitchen and avoid obstacles.]
        
    Once you have a clear view of the kitchen, tell me that you have found it, and perform no further actions.
    You must use one of the function/tool calls provided to execute actions."""

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
        "content": [{
            "type": "text",
            "text": "RGB Image (left), Depth Image (right) with distance scale in meters. Find the toy kitchen and stay well clear of obstacles."
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
    # Removes the encoded image to save space and reduce context window 
    messages = modify_last_entry(messages)

    choice_message = response.choices[0].message

    # Handle the case where content might be None
    message_content = choice_message.content if choice_message.content is not None else "No content provided."

    # Base structure for new message
    new_message = {
        "chat_completion_id": response.id,
        "created": response.created,
        "model": response.model,
        "system_fingerprint": response.system_fingerprint,
        "usage": {
            "completion_tokens": response.usage.completion_tokens,
            "prompt_tokens": response.usage.prompt_tokens,
            "total_tokens": response.usage.total_tokens,
        },
        "role": choice_message.role,
        "content": [
            {
                "type": "text",
                "text": message_content
            }
        ]
    }

    # Add tool calls, if any
    tool_calls = getattr(choice_message, 'tool_calls', None)
    if tool_calls:
        new_message["tool_calls"] = [
            {
                "id": tool_call.id,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments
                },
                "type": tool_call.type
            } for tool_call in tool_calls
        ]

    pretty_print_conversation([new_message])
    messages.append(new_message)
    
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
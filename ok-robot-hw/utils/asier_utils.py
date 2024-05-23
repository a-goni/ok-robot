def get_A_near_B_objects():
    """
    The robot takes input from human, human will send text queries to the robot when this function is called.
    A is the name of the object human wants the robot to pick up / place on.
    B can be used to specify an object close to A and serve as functionality "A near B".
    If you leave B empty, the robot will simply localize A.
    """
    try:
        A = input("Enter A: ").strip()
        print(f"A = {A}")
        B = input("Enter B: ").strip()
        print(f"B = {B}")
        return A, B
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Exiting.")
        exit(0)

def get_A_object():
    """
    The robot takes input from human, human will send text queries to the robot when this function is called.
    A is the name of the object human wants the robot to pick up / place on.
    """
    try:
        A = input("Enter A: ").strip()
        print(f"A = {A}")
        return A
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Exiting.")
        exit(0)

def get_yes_or_no(prompt):
    """Prompt the user until they provide a valid response (Y or N)."""
    while True:
        try:
            response = input(prompt).strip().upper()
            if response == 'Y' or response == 'N':
                return response
            else:
                print("Invalid input. Please enter 'Y' or 'N'.")
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received. Exiting.")
            exit(0)
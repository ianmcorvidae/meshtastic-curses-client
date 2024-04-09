import curses
from meshtastic import config_pb2, module_config_pb2
import meshtastic.serial_interface, meshtastic.tcp_interface



def display_enum_menu(stdscr, enum_values, setting_string):
    apply_settings = False
    menu_height = len(enum_values) + 2
    menu_width = max(len(option) for option in enum_values) + 4
    y_start = (curses.LINES - menu_height) // 2
    x_start = (curses.COLS - menu_width) // 2

    try:
        menu_win = curses.newwin(menu_height, menu_width, y_start, x_start)
    except curses.error as e:
        print("Error occurred while initializing curses window:", e)

    menu_win.border()
    menu_win.keypad(True)
    curses.curs_set(0)
    menu_win.refresh()

    menu_item = 0
    for i, option in enumerate(enum_values, start=0):
        if i == setting_string:
            menu_win.addstr(i+1, 1, option, curses.A_REVERSE)
            menu_item = i
        else:
            menu_win.addstr(i+1, 1, option)
    
    menu_win.refresh()

    while True:
        char = menu_win.getch()
        if char == curses.KEY_DOWN:
            menu_item = min(len(enum_values) - 1, menu_item + 1)
        elif char == curses.KEY_UP:
            menu_item = max(0, menu_item - 1)
        elif char == ord('\n'):
            break

        elif char == 27:
            return None, False

        if char:
            menu_win.clear()
            menu_win.border()


        for i, option in enumerate(enum_values, start=1):
            if i == menu_item + 1:
                menu_win.addstr(i, 1, option, curses.A_REVERSE)
            else:
                menu_win.addstr(i, 1, option)

    selected_option = enum_values[menu_item]
    menu_win.clear()
    menu_win.refresh()

    return selected_option, True



def get_string_input(stdscr, setting_string):
    popup_height = 5
    popup_width = 40
    y_start = (curses.LINES - popup_height) // 2
    x_start = (curses.COLS - popup_width) // 2

    try:
        input_win = curses.newwin(popup_height, popup_width, y_start, x_start)
    except curses.error as e:
        print("Error occurred while initializing curses window:", e)

    input_win.border()
    input_win.keypad(True)
    input_win.refresh()

    curses.echo()
    input_win.addstr(1, 1, str(setting_string))  # Prepopulate input field with the setting value
    input_win.refresh()
    char = input_win.getch()
    if char == 27:  # Check if escape key is pressed
        curses.noecho()
        return None, False
    input_win.clear()
    input_win.border()
    input_win.refresh()
    input_str = input_win.getstr(1, 1, 30).decode("utf-8")
    curses.noecho()

    input_win.clear()
    input_win.refresh()
    return input_str, True


def get_uint_input(stdscr, setting_string):
    popup_height = 5
    popup_width = 40
    y_start = (curses.LINES - popup_height) // 2
    x_start = (curses.COLS - popup_width) // 2

    try:
        input_win = curses.newwin(popup_height, popup_width, y_start, x_start)
    except curses.error as e:
        print("Error occurred while initializing curses window:", e)

    input_win.border()
    input_win.keypad(True)
    input_win.refresh()

    curses.echo()
    input_win.addstr(1, 1, str(setting_string))  # Prepopulate input field with the setting value
    input_win.refresh()
    char = input_win.getch()
    if char == 27:  # Check if escape key is pressed
        curses.noecho()
        return None, False
    input_win.clear()
    input_win.border()
    input_win.refresh()
    input_str = input_win.getstr(1, 1, 30).decode("utf-8")
    curses.noecho()

    try:
        input_uint = int(input_str)
    except ValueError:
        input_uint = None

    input_win.clear()
    input_win.refresh()
    return input_uint, True




def display_bool_menu(stdscr, setting_value):
    bool_options = ["False", "True"]
    return display_enum_menu(stdscr, bool_options, setting_value)



def generate_menu_from_protobuf(message_instance, interface):
    if not hasattr(message_instance, "DESCRIPTOR"):
        return  # This is not a protobuf message instance, exit
    menu = {}

    field_names = message_instance.DESCRIPTOR.fields_by_name.keys()
    for field_name in field_names:
        field_descriptor = message_instance.DESCRIPTOR.fields_by_name[field_name]
        if field_descriptor is not None:
            nested_message_instance = getattr(message_instance, field_name)
            menu[field_name] = generate_menu_from_protobuf(nested_message_instance, interface)

    return menu


def change_setting(stdscr, interface, menu_path):
    node = interface.getNode('^local')
    field_descriptor = None
    
    stdscr.clear()
    stdscr.border()
    menu_header(stdscr, f"{menu_path[3]}")

    if menu_path[1] == "Radio Settings":
        setting_string = getattr(getattr(node.localConfig, str(menu_path[2])), menu_path[3])
        field_descriptor = getattr(node.localConfig, menu_path[2]).DESCRIPTOR.fields_by_name[menu_path[3]]

    elif menu_path[1] == "Module Settings":
        setting_string = getattr(getattr(node.moduleConfig, str(menu_path[2])), menu_path[3])
        field_descriptor = getattr(node.moduleConfig, menu_path[2]).DESCRIPTOR.fields_by_name[menu_path[3]]


    if field_descriptor.enum_type is not None:
        enum_values = [enum_value.name for enum_value in field_descriptor.enum_type.values]
        enum_option, change_setting = display_enum_menu(stdscr, enum_values, setting_string)
        setting_value = enum_option
        if not change_setting:
            stdscr.clear()
            stdscr.border()
            menu_path.pop()
            return  # Exit function if escape was pressed during input

    elif field_descriptor.type == 8:  # Field type 8 corresponds to BOOL
        setting_value, change_setting = display_bool_menu(stdscr, setting_string)
        if not change_setting:
            stdscr.clear()
            stdscr.border()
            menu_path.pop()
            return  # Exit function if escape was pressed during input

    elif field_descriptor.type == 9:  # Field type 9 corresponds to STRING
        setting_value, change_setting = get_string_input(stdscr, setting_string)
        if not change_setting:
            stdscr.clear()
            stdscr.border()
            menu_path.pop()
            return  # Exit function if escape was pressed during input

    elif field_descriptor.type == 13:  # Field type 13 corresponds to UINT32
        setting_value, change_setting = get_uint_input(stdscr, setting_string)
        if not change_setting:
            stdscr.clear()
            stdscr.border()
            menu_path.pop()
            return  # Exit function if escape was pressed during input

    formatted_text = f"{menu_path[2]}.{menu_path[3]} = {setting_value}"
    menu_header(stdscr,formatted_text,2)



    ourNode = interface.getNode('^local')
    
    # Convert "true" to 1, "false" to 0, leave other values as they are
    if setting_value == "True" or setting_value == "1":
        setting_value_int = 1
    elif setting_value == "False" or setting_value == "0":
        setting_value_int = 0
    else:
        # If setting_value is not "true" or "false", keep it as it is
        setting_value_int = setting_value


    try:
        if menu_path[1] == "Radio Settings":
            setattr(getattr(ourNode.localConfig, menu_path[2]), menu_path[3], setting_value_int)
        elif menu_path[1] == "Module Settings":
            setattr(getattr(ourNode.moduleConfig, menu_path[2]), menu_path[3], setting_value_int)
    except AttributeError as e:
        print("Error setting attribute:", e)




    ourNode.writeConfig(menu_path[2])
    menu_path.pop()






def display_values(stdscr, interface, key_list, menu_path, setting_name = None):
    node = interface.getNode('^local')
    for i, key in enumerate(key_list):
        if menu_path[1] == "Radio Settings":
            setting = getattr(getattr(node.localConfig, str(setting_name)), key_list[i])  
        if menu_path[1] == "Module Settings":
            setting = getattr(getattr(node.moduleConfig, str(setting_name)), key_list[i])
        stdscr.addstr(i+3, 40, str(setting))
    stdscr.refresh()

def menu_header(window, text, start_y=1):
    _, window_width = window.getmaxyx()
    start_x = (window_width - len(text)) // 2
    formatted_text = text.replace('_', ' ').title()
    window.addstr(start_y, start_x, formatted_text)
    window.refresh()

def nested_menu(stdscr, menu, interface):
    menu_item = 0
    current_menu = menu
    prev_menu = []
    menu_index = 0

    setting_name = None
    key_list = []
    menu_path = ["Main Menu"]

    while True:
        # Display current menu
        if current_menu is not None:
            for i, key in enumerate(current_menu.keys(), start=0):
                if i == menu_item:
                    if key in ["Reboot", "Reset NodeDB", "Shutdown", "Factory Reset"]:
                        stdscr.addstr(i+3, 1, key, curses.color_pair(5))
                    else:
                        stdscr.addstr(i+3, 1, key, curses.A_REVERSE)
                else:
                    stdscr.addstr(i+3, 1, key)

            menu_header(stdscr, f"{menu_path[menu_index]}")

            char = stdscr.getch()

            selected_key = list(current_menu.keys())[menu_item]
            selected_value = current_menu[selected_key]

            if char == curses.KEY_DOWN:
                menu_item = min(len(current_menu) - 1, menu_item + 1)

            elif char == curses.KEY_UP:
                menu_item = max(0, menu_item - 1)

            elif char == curses.KEY_RIGHT:
                if isinstance(selected_value, dict):
                    # If the selected item is a submenu, navigate to it
                    prev_menu.append(current_menu)
                    menu_index += 1
                    current_menu = selected_value
                    menu_item = 0
                    
                if len(menu_path) < 4 and selected_key not in ["Reboot", "Reset NodeDB", "Shutdown", "Factory Reset"]:
                    menu_path.append(selected_key)

            elif char == curses.KEY_LEFT:
                if len(menu_path) == 4:
                    menu_path.pop()
                if len(menu_path) > 1:
                    menu_path.pop()
                    current_menu = prev_menu[menu_index-1]
                    del prev_menu[menu_index-1]
                    menu_index -= 1
                    menu_item = 0


            elif char == ord('\n'):
                # If user presses enter, display the selected value if it's not a submenu
                if selected_key == "Reboot":
                    settings_reboot(interface)
                elif selected_key == "Reset NodeDB":
                    settings_reset_nodedb(interface)
                elif selected_key == "Shutdown":
                    settings_shutdown(interface)
                elif selected_key == "Factory Reset":
                    settings_factory_reset(interface)

                elif selected_value is not None:
                    stdscr.refresh()
                    stdscr.getch()  # Wait for user input before continuing
            # escape to exit menu        
            elif char == 27:
                break

            if char:
                stdscr.clear()
                stdscr.border()

            next_key = list(current_menu.keys())[menu_item]
            key_list = list(current_menu.keys())

            if menu_index==1:
                setting_name = next_key
            elif menu_index==2:
                display_values(stdscr, interface, key_list, menu_path, setting_name)
        else:
            break  # Exit loop if current_menu is None

        if len(menu_path) == 4:
            change_setting(stdscr, interface, menu_path)

def settings(stdscr, interface):
    popup_height = 25
    popup_width = 60
    y_start = (curses.LINES - popup_height) // 2
    x_start = (curses.COLS - popup_width) // 2
    try:
        popup_win = curses.newwin(popup_height, popup_width, y_start, x_start)
    except curses.error as e:
        print("Error occurred while initializing curses window:", e)

    popup_win.border()
    popup_win.keypad(True)
    
    # Generate menu from protobuf for both radio and module settings
    radio = config_pb2.Config()
    radio_config = generate_menu_from_protobuf(radio, interface)

    module = module_config_pb2.ModuleConfig()
    module_config = generate_menu_from_protobuf(module, interface)

    # Add top-level menu items
    top_level_menu = {
        "Radio Settings": radio_config,
        "Module Settings": module_config,
        "Reboot": None,
        "Reset NodeDB": None,
        "Shutdown": None,
        "Factory Reset": None
    }

    # Call nested_menu function to display and handle the nested menu
    nested_menu(popup_win, top_level_menu, interface)

    # Close the popup window
    popup_win.clear()
    popup_win.refresh()
    del popup_win  # Delete the window object to free up memory


def settings_reboot(interface):
    interface.getNode('^local').reboot()

def settings_reset_nodedb(interface):
    interface.getNode('^local').resetNodeDb()

def settings_shutdown(interface):
    interface.getNode('^local').shutdown()

def settings_factory_reset(interface):
    interface.getNode('^local').factory_reset()



if __name__ == "__main__":

    interface = meshtastic.serial_interface.SerialInterface()
    # radio = config_pb2.Config()
    # module = module_config_pb2.ModuleConfig()
    # print(generate_menu_from_protobuf(radio))
    # print(generate_menu_from_protobuf(module))

    def main(stdscr):
        stdscr.keypad(True)
        while True:
            settings(stdscr, interface)
        
    curses.wrapper(main)
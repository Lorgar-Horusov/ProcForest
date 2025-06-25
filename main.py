from src.process_parser import list_process, text_sparkline
from textual.app import App, ComposeResult
from textual.widgets import Tree, Footer, OptionList
from textual.containers import ScrollableContainer
from textual.binding import Binding


class ProcessTreeApp(App):
    """
    A Textual TUI application that displays a tree of system processes.
    Provides options to expand/collapse the tree and sort by name, memory, PID, owner.

    Key Bindings:
        - 'q': Quit the app.
        - 'e': Expand all nodes.
        - 'c': Collapse all nodes.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sort_by = "pid"

    BINDINGS = [
        Binding("q,й", "quit", "Quit the app"),
        Binding("e,у", "expand_all", "Expand all nodes"),
        Binding("c,с", "collapse_all", "Collapse all nodes"),
    ]

    def compose(self) -> ComposeResult:
        yield ScrollableContainer(Tree("Process Tree"))
        yield OptionList("По PID", "По Алфавиту", "По Владельцу", "По Памяти")
        yield Footer()

    def on_mount(self):
        self.load_tree()

    def load_tree(self):
        tree = self.query_one(Tree)
        tree.clear()
        processes, children_map = list_process()
        root_pids = [
            pid for pid in processes if processes[pid]["ppid"] not in processes
        ]

        def sorter(pid):
            proc = processes[pid]
            match self.sort_by:
                case "alphabet":
                    return proc["name"].lower()
                case "owner":
                    return proc["username"].lower()
                case "memory":
                    return proc.get("memory_total", 0)
                case _:
                    return proc["pid"]

        reverse = self.sort_by == "memory"
        for pid in sorted(root_pids, key=sorter, reverse=reverse):
            proc = processes[pid]
            node = tree.root.add(self.format_proc(proc))
            self.add_children_recursive(node, pid, processes, children_map)

    def add_children_recursive(self, tree_node, pid, processes, children_map):
        if pid not in children_map:
            return
        child_pids = children_map[pid]

        def sorter(pid):
            proc = processes[pid]
            match self.sort_by:
                case "alphabet":
                    return proc["name"].lower()
                case "owner":
                    return proc["username"].lower()
                case "memory":
                    return proc.get("memory_total", 0)
                case _:
                    return proc["pid"]

        reverse = self.sort_by == "memory"
        for child_pid in sorted(child_pids, key=sorter, reverse=reverse):
            child_proc = processes[child_pid]
            child_node = tree_node.add(self.format_proc(child_proc))
            self.add_children_recursive(child_node, child_pid, processes, children_map)

    def format_proc(self, proc):
        return (
            f"{proc['name'].ljust(25)}"
            f"PID: {str(proc['pid']).ljust(10)}"
            f"owner: {proc['username'].ljust(12)}"
            f"memory: {text_sparkline(proc['memory_total'])} {proc['memory_total']}%"
        )

    def action_expand_all(self):
        tree = self.query_one(Tree)
        tree.root.expand_all()

    def action_collapse_all(self):
        tree = self.query_one(Tree)
        tree.root.collapse_all()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        selected = event.option.prompt
        match selected:
            case "По Алфавиту":
                self.sort_by = "alphabet"
            case "По PID":
                self.sort_by = "pid"
            case "По Владельцу":
                self.sort_by = "owner"
            case "По Памяти":
                self.sort_by = "memory"
        self.load_tree()


if __name__ == "__main__":
    app = ProcessTreeApp()
    app.run()

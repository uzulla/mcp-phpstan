#!/usr/bin/env python3
"""
Text User Interface (TUI) for MCP PHPStan Integration.

This module provides a text-based user interface for the MCP PHPStan Integration tool.
It allows users to interactively run PHPStan analysis, view errors, and fix them using Claude.
"""

import os
import sys
import json
import argparse
import time
import curses
import dotenv
from typing import Dict, List, Any, Optional, Tuple

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.McpIntegration.McpClient import McpClient
from src.PhpStanRunner.Runner import PhpStanRunner

# Load environment variables from .env file if it exists
dotenv.load_dotenv()


class TuiClient:
    """Text User Interface (TUI) for MCP PHPStan Integration."""

    def __init__(self, 
                 stdscr,
                 project_path: str,
                 max_errors_per_batch: int = 3,
                 max_iterations: int = 10):
        """
        Initialize the TUI.
        
        Args:
            stdscr: Curses standard screen
            project_path: Path to the PHP project
            max_errors_per_batch: Maximum number of errors to process in a single batch
            max_iterations: Maximum number of iterations to run
        """
        self.stdscr = stdscr
        self.project_path = os.path.abspath(project_path)
        self.max_errors_per_batch = max_errors_per_batch
        self.max_iterations = max_iterations
        
        # Check if .env file exists
        env_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
        env_example_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env.example')
        
        if not os.path.exists(env_file_path):
            self.cleanup()
            print("Error: .env file not found.")
            print("Please create a .env file by copying .env.example:")
            print("")
            print(f"    cp {env_example_path} {env_file_path}")
            print("")
            print("Then edit the .env file and add your Claude API key:")
            print("")
            print("    CLAUDE_API_KEY=your_api_key_here")
            print("")
            sys.exit(1)
            
        # Check if Claude API key is set
        if not os.environ.get("CLAUDE_API_KEY"):
            self.cleanup()
            print("Error: CLAUDE_API_KEY environment variable not set.")
            print("Your .env file exists but may not contain the API key.")
            print("Please add the following line to your .env file:")
            print("")
            print("    CLAUDE_API_KEY=your_api_key_here")
            print("")
            sys.exit(1)
        
        # Initialize MCP client
        self.mcp_client = McpClient(self.project_path, self.max_errors_per_batch)
        
        # Initialize PHPStan runner
        self.phpstan_runner = PhpStanRunner(self.project_path)
        
        # Initialize curses
        curses.curs_set(0)  # Hide cursor
        curses.start_color()
        curses.use_default_colors()
        
        # Define color pairs
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)    # Status bar
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)   # Command bar
        curses.init_pair(3, curses.COLOR_RED, -1)                     # Error
        curses.init_pair(4, curses.COLOR_GREEN, -1)                   # Success
        curses.init_pair(5, curses.COLOR_YELLOW, -1)                  # Warning
        curses.init_pair(6, curses.COLOR_CYAN, -1)                    # Info
        
        # Get screen dimensions
        self.height, self.width = self.stdscr.getmaxyx()
        
        # Initialize state
        self.view = "errors"  # Current view: "errors", "log", "help"
        self.command_mode = False  # Whether we're in command mode
        self.command = ""  # Current command
        self.status = "Ready"  # Current status
        self.log = []  # Log messages
        self.batches = []  # Error batches
        self.current_batch_idx = 0  # Index of the current batch
        self.scroll_offset = 0  # Scroll offset for the current view
        
        # Add initial log message
        self.add_log(f"TUI initialized for {self.project_path}")
        self.add_log(f"Max errors per batch: {self.max_errors_per_batch}")
        self.add_log(f"Max iterations: {self.max_iterations}")
        self.add_log("Press 'h' for help")

    def cleanup(self):
        """Clean up curses."""
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    def add_log(self, message: str):
        """
        Add a message to the log.
        
        Args:
            message: Message to add to the log
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log.append(f"[{timestamp}] {message}")

    def draw_status_bar(self):
        """Draw the status bar."""
        status_bar = f" {self.status} | View: {self.view.capitalize()} | Batch: {self.current_batch_idx + 1}/{len(self.batches) if self.batches else 0} "
        status_bar = status_bar + " " * (self.width - len(status_bar) - 1)
        self.stdscr.attron(curses.color_pair(1))
        self.stdscr.addstr(0, 0, status_bar)
        self.stdscr.attroff(curses.color_pair(1))

    def draw_command_bar(self):
        """Draw the command bar."""
        if self.command_mode:
            command_bar = f" :{self.command}"
        else:
            command_bar = " Press ':' to enter command mode | q: Quit | h: Help | e: Errors | l: Log | r: Run | f: Fix | a: Fix All "
        
        command_bar = command_bar + " " * (self.width - len(command_bar) - 1)
        self.stdscr.attron(curses.color_pair(2))
        self.stdscr.addstr(self.height - 1, 0, command_bar)
        self.stdscr.attroff(curses.color_pair(2))

    def draw_errors_view(self):
        """Draw the errors view."""
        if not self.batches:
            self.stdscr.addstr(2, 2, "No errors found. Press 'r' to run PHPStan analysis.")
            return
        
        # Get the current batch
        batch = self.batches[self.current_batch_idx]
        
        # Draw batch info
        batch_info = batch["batch"]
        self.stdscr.addstr(2, 2, f"Batch {batch_info['index'] + 1}/{batch_info['total']} - {batch_info['count']} errors")
        
        # Draw errors by file
        y = 4
        for file_path, errors in batch["errors_by_file"].items():
            if y >= self.height - 2:
                break
            
            self.stdscr.attron(curses.A_BOLD)
            self.stdscr.addstr(y, 2, f"File: {file_path}")
            self.stdscr.attroff(curses.A_BOLD)
            y += 1
            
            for error in errors:
                if y >= self.height - 2:
                    break
                
                line = error.get("line", "?")
                message = error.get("message", "Unknown error")
                
                self.stdscr.attron(curses.color_pair(3))
                self.stdscr.addstr(y, 4, f"Line {line}: {message}")
                self.stdscr.attroff(curses.color_pair(3))
                y += 1
            
            y += 1

    def draw_log_view(self):
        """Draw the log view."""
        if not self.log:
            self.stdscr.addstr(2, 2, "No log messages.")
            return
        
        # Calculate visible log entries
        visible_height = self.height - 3
        start_idx = max(0, len(self.log) - visible_height - self.scroll_offset)
        end_idx = min(len(self.log), start_idx + visible_height)
        
        # Draw log entries
        for i, log_entry in enumerate(self.log[start_idx:end_idx]):
            y = 2 + i
            
            # Color based on log entry content
            if "error" in log_entry.lower() or "failed" in log_entry.lower():
                self.stdscr.attron(curses.color_pair(3))
            elif "success" in log_entry.lower() or "fixed" in log_entry.lower():
                self.stdscr.attron(curses.color_pair(4))
            elif "warning" in log_entry.lower():
                self.stdscr.attron(curses.color_pair(5))
            else:
                self.stdscr.attron(curses.color_pair(6))
            
            self.stdscr.addstr(y, 2, log_entry[:self.width - 4])
            
            # Reset color
            self.stdscr.attroff(curses.color_pair(3))
            self.stdscr.attroff(curses.color_pair(4))
            self.stdscr.attroff(curses.color_pair(5))
            self.stdscr.attroff(curses.color_pair(6))

    def draw_help_view(self):
        """Draw the help view."""
        help_text = [
            "MCP PHPStan Integration TUI Help",
            "",
            "Keyboard Controls:",
            "  q: Quit",
            "  h: Show this help",
            "  e: Show errors view",
            "  l: Show log view",
            "  r: Run PHPStan analysis",
            "  f: Fix current batch of errors",
            "  a: Fix all batches of errors",
            "  n: Go to next batch of errors",
            "  p: Go to previous batch of errors",
            "  :: Enter command mode",
            "",
            "Commands:",
            "  :run - Run PHPStan analysis",
            "  :fix - Fix current batch of errors",
            "  :fixall - Fix all batches of errors",
            "  :next - Go to next batch of errors",
            "  :prev - Go to previous batch of errors",
            "  :quit - Quit",
            "  :help - Show this help"
        ]
        
        for i, line in enumerate(help_text):
            if 2 + i >= self.height - 1:
                break
            
            if i == 0:
                self.stdscr.attron(curses.A_BOLD)
                self.stdscr.addstr(2 + i, 2, line)
                self.stdscr.attroff(curses.A_BOLD)
            elif line.startswith("  :"):
                self.stdscr.attron(curses.color_pair(6))
                self.stdscr.addstr(2 + i, 2, line)
                self.stdscr.attroff(curses.color_pair(6))
            elif line.startswith("  "):
                self.stdscr.attron(curses.color_pair(5))
                self.stdscr.addstr(2 + i, 2, line[:3])
                self.stdscr.attroff(curses.color_pair(5))
                self.stdscr.addstr(2 + i, 5, line[3:])
            else:
                self.stdscr.addstr(2 + i, 2, line)

    def draw(self):
        """Draw the TUI."""
        self.stdscr.clear()
        
        # Draw status bar
        self.draw_status_bar()
        
        # Draw main content
        if self.view == "errors":
            self.draw_errors_view()
        elif self.view == "log":
            self.draw_log_view()
        elif self.view == "help":
            self.draw_help_view()
        
        # Draw command bar
        self.draw_command_bar()
        
        self.stdscr.refresh()

    def run_phpstan_analysis(self, 
                            paths: Optional[List[str]] = None,
                            level: Optional[int] = None,
                            config_path: Optional[str] = None) -> bool:
        """
        Run PHPStan analysis and format the errors.
        
        Args:
            paths: List of paths to analyze
            level: PHPStan rule level (0-9)
            config_path: Path to PHPStan config file
            
        Returns:
            True if analysis was successful, False otherwise
        """
        self.status = "Running PHPStan analysis..."
        self.draw()
        
        self.add_log(f"Running PHPStan analysis on {self.project_path}...")
        
        try:
            # Run PHPStan analysis
            output, return_code, batches = self.mcp_client.run_phpstan_analysis(
                paths, level, config_path, False
            )
            
            # Log the results
            if return_code == 0:
                self.add_log("No PHPStan errors found!")
                self.batches = []
                self.current_batch_idx = 0
                self.status = "Ready - No errors found"
                return True
            
            total_errors = sum(len(batch['errors_by_file'][file]) for batch in batches for file in batch['errors_by_file'])
            self.add_log(f"Found {total_errors} errors in {len(batches)} batches.")
            
            self.batches = batches
            self.current_batch_idx = 0
            self.status = f"Ready - Found {total_errors} errors"
            return True
            
        except Exception as e:
            self.add_log(f"Error running PHPStan analysis: {str(e)}")
            self.status = "Error running PHPStan analysis"
            return False

    def fix_current_batch(self) -> bool:
        """
        Fix the current batch of errors using Claude.
        
        Returns:
            True if fixes were applied successfully, False otherwise
        """
        if not self.batches:
            self.add_log("No errors to fix!")
            return False
        
        batch = self.batches[self.current_batch_idx]
        batch_idx = batch["batch"]["index"]
        total_batches = batch["batch"]["total"]
        
        self.status = f"Fixing batch {batch_idx + 1}/{total_batches}..."
        self.draw()
        
        self.add_log(f"Processing batch {batch_idx + 1}/{total_batches}...")
        
        try:
            # Prepare MCP message
            message = self.mcp_client.prepare_mcp_message(batch)
            
            # Send to Claude
            self.add_log("Sending errors to Claude...")
            response = self.mcp_client.send_to_claude(message)
            
            # Check if Claude returned an error
            if response.get("status") == "error":
                self.add_log(f"Error from Claude: {response.get('message')}")
                self.status = "Error from Claude"
                return False
            
            # Apply fixes
            if "fixes" in response and response["fixes"]:
                self.add_log(f"Applying {len(response['fixes'])} fixes suggested by Claude...")
                success = self.mcp_client.apply_fixes(response["fixes"])
                
                if success:
                    self.add_log("Fixes applied successfully!")
                    self.status = "Fixes applied successfully"
                    return True
                else:
                    self.add_log("Failed to apply fixes.")
                    self.status = "Failed to apply fixes"
                    return False
            else:
                self.add_log("No fixes suggested by Claude.")
                self.status = "No fixes suggested by Claude"
                return False
                
        except Exception as e:
            self.add_log(f"Error fixing batch: {str(e)}")
            self.status = "Error fixing batch"
            return False

    def fix_all_batches(self) -> bool:
        """
        Fix all batches of errors.
        
        Returns:
            True if all batches were fixed successfully, False otherwise
        """
        if not self.batches:
            self.add_log("No errors to fix!")
            return True
        
        self.add_log(f"Fixing {len(self.batches)} batches of errors...")
        
        iteration = 0
        while iteration < self.max_iterations and self.batches:
            self.add_log(f"\nIteration {iteration + 1}/{self.max_iterations}")
            
            # Fix each batch
            for i in range(len(self.batches)):
                self.current_batch_idx = i
                self.fix_current_batch()
                self.draw()
            
            # Run PHPStan again to check if all errors are fixed
            self.run_phpstan_analysis()
            
            if not self.batches:
                self.add_log("All errors fixed!")
                self.status = "All errors fixed!"
                return True
            
            iteration += 1
        
        if self.batches:
            self.add_log(f"Reached maximum iterations ({self.max_iterations}) without fixing all errors.")
            self.status = "Max iterations reached"
            return False
        
        return True

    def handle_command(self, command: str) -> bool:
        """
        Handle a command.
        
        Args:
            command: Command to handle
            
        Returns:
            True if the command was handled successfully, False otherwise
        """
        command = command.strip().lower()
        
        if command == "quit":
            return False
        elif command == "help":
            self.view = "help"
        elif command == "errors":
            self.view = "errors"
        elif command == "log":
            self.view = "log"
        elif command == "run":
            self.run_phpstan_analysis()
        elif command == "fix":
            self.fix_current_batch()
        elif command == "fixall":
            self.fix_all_batches()
        elif command == "next":
            if self.batches and self.current_batch_idx < len(self.batches) - 1:
                self.current_batch_idx += 1
        elif command == "prev":
            if self.batches and self.current_batch_idx > 0:
                self.current_batch_idx -= 1
        else:
            self.add_log(f"Unknown command: {command}")
        
        return True

    def run(self) -> None:
        """Run the TUI main loop."""
        try:
            while True:
                # Draw the TUI
                self.draw()
                
                # Get user input
                key = self.stdscr.getch()
                
                # Handle command mode
                if self.command_mode:
                    if key == 27:  # Escape
                        self.command_mode = False
                        self.command = ""
                    elif key == 10:  # Enter
                        self.command_mode = False
                        if not self.handle_command(self.command):
                            break
                        self.command = ""
                    elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace
                        self.command = self.command[:-1]
                    elif key >= 32 and key <= 126:  # Printable ASCII
                        self.command += chr(key)
                    continue
                
                # Handle normal mode
                if key == ord('q'):
                    break
                elif key == ord(':'):
                    self.command_mode = True
                    self.command = ""
                elif key == ord('h'):
                    self.view = "help"
                elif key == ord('e'):
                    self.view = "errors"
                elif key == ord('l'):
                    self.view = "log"
                elif key == ord('r'):
                    self.run_phpstan_analysis()
                elif key == ord('f'):
                    self.fix_current_batch()
                elif key == ord('a'):
                    self.fix_all_batches()
                elif key == ord('n'):
                    if self.batches and self.current_batch_idx < len(self.batches) - 1:
                        self.current_batch_idx += 1
                elif key == ord('p'):
                    if self.batches and self.current_batch_idx > 0:
                        self.current_batch_idx -= 1
                
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()


def main():
    """Main entry point for the TUI."""
    parser = argparse.ArgumentParser(description="TUI for MCP PHPStan Integration")
    parser.add_argument("project_path", help="Path to the PHP project")
    parser.add_argument("--max-errors", "-m", type=int, default=3, help="Maximum errors per batch")
    parser.add_argument("--max-iterations", "-i", type=int, default=10, help="Maximum iterations")
    
    args = parser.parse_args()
    
    # Run the TUI
    curses.wrapper(lambda stdscr: TuiClient(
        stdscr,
        args.project_path,
        args.max_errors,
        args.max_iterations
    ).run())


if __name__ == "__main__":
    main()

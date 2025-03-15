<?php

namespace App\Controllers;

use App\Models\User;
use App\Utils\Logger;

class UserController
{
    private Logger $logger;

    public function __construct()
    {
        // Initialize Logger
        $this->logger = new Logger();
    }

    /**
 * @param array<string, mixed> $data
 */
public function createUser(array $data = []): User
    {
        // Undefined variable
        $this->logger->log("Creating user: " . $data["name"]);

        // Missing required parameter
        $user = new User($data["name"] ?? "Unknown User");

        if (isset($data['roles'])) {
            foreach ($data['roles'] as $role) {
                $user->addRole($role);
            }
        }

        // Calling undefined method
        // $user->setEmail($data['email'] ?? ''); // Method does not exist in User class

        return $user;
    }

    // Missing return type
    public function getUser(int $id): User
    {
        // Undefined class
        $repository = new \App\Models\User("User from Repository", 25); // Using User as a temporary replacement for UserRepository;
        
        // Method call on non-object
        $result = $repository; // Repository is now a User object that can be returned directly
        
        return new User('Test User', 30);
    }
}

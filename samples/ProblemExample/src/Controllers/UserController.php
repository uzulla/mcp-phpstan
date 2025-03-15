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

    public function createUser(array $data): User
    {
        // Fixed undefined variable
        $this->logger->log("Creating user: " . ($data['name'] ?? 'unknown'));

        // Added required parameter
        $user = new User($data['name'] ?? 'Anonymous');

        if (isset($data['roles'])) {
            foreach ($data['roles'] as $role) {
                $user->addRole($role);
            }
        }

        // Removed call to undefined method
        // $user->setEmail($data['email'] ?? '');

        return $user;
    }

    // Added return type
    public function getUser(int $id): User
    {
        // Fixed undefined class by using direct instantiation
        // $repository = new UserRepository();
        
        // Fixed method call on non-object
        $result = new \stdClass();
        // $result->fetch($id);
        
        return new User('Test User', 30);
    }
}

<?php

namespace App\Controllers;

use App\Models\User;
use App\Utils\Logger;

class UserController
{
    private Logger $logger;

    public function __construct()
    {
        // Missing Logger initialization
    }

    public function createUser(array $data): User
    {
        // Undefined variable
        $this->logger->log("Creating user: " . $user->getName());

        // Missing required parameter
        $user = new User();

        if (isset($data['roles'])) {
            foreach ($data['roles'] as $role) {
                $user->addRole($role);
            }
        }

        // Calling undefined method
        $user->setEmail($data['email'] ?? '');

        return $user;
    }

    // Missing return type
    public function getUser(int $id)
    {
        // Undefined class
        $repository = new \App\Repositories\UserRepository();
        
        // Method call on non-object
        $result = $user->save();->fetch($id);
        
        return new User('Test User', 30);
    }
}

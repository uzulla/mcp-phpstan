<?php

namespace App\Models;

class User
{
    private string $name;
    private ?int $age;
    private array $roles;

    public function __construct(string $name, ?int $age = null)
    {
        $this->name = $name;
        $this->age = $age;
        // Missing initialization of $roles property
    }

    public function getName(): string
    {
        return $this->name;
    }

    public function getAge(): ?int
    {
        return $this->age;
    }

    // Return type mismatch - should be array
    public function getRoles(): string
    {
        return $this->roles;
    }

    // Parameter type mismatch
    public function addRole(string $role): void
    {
        $this->roles[] = $role;
    }

    // Undefined variable usage
    public function hasRole(string $roleName): bool
    {
        return in_array($roleName, $roles);
    }
}

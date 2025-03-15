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
        $this->roles = []; // Initialize roles array
    }

    public function getName(): string
    {
        return $this->name;
    }

    public function getAge(): ?int
    {
        return $this->age;
    }

    /**
     * @return string[] Array of user roles
     */
    public function getRoles(): string
    {
        return $this->roles;
    }

    // Parameter type mismatch
    public function addRole(string $role): void
    {
        $this->roles[] = $role;
    }

    // Fixed undefined variable usage
    public function hasRole(string $roleName): bool
    {
        return in_array($roleName, $this->roles);
    }
}

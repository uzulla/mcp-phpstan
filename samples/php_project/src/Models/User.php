<?php

namespace App\Models;

class User
{
    private string $name;
    private ?int $age;
    /** @var array<string> */
    private array $roles;

    public function __construct(string $name, ?int $age = null)
    {
        $this->name = $name;
        $this->age = $age;
        $this->roles = [];
        // Roles property initialized
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
    /** @return array<string> */
    public function getRoles(): array
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
        return in_array($roleName, $this->roles);
    }
}

<?php

require_once __DIR__ . '/vendor/autoload.php';

use MCP\PHPStan\IncrementalProcessor;

// Path to the sample PHP project
$projectPath = __DIR__ . '/../samples/php_project';

echo "PHP実装を使用してPHPStanエラーを修正します\n";
echo "================================================\n";

// Step 1: Run PHPStan to detect errors
echo "Step 1: PHPStanを実行してエラーを検出します...\n";
$phpstanBinary = $projectPath . '/vendor/bin/phpstan';
$cmd = "$phpstanBinary analyse $projectPath/src/ --level=5";
exec($cmd, $output, $returnCode);
echo implode("\n", $output) . "\n\n";

// Step 2: Create mock fixes (simulating Claude API response)
echo "Step 2: エラー修正案を生成します (Claude API のシミュレーション)...\n";
$mockFixes = [
    [
        'file' => 'src/Models/User.php',
        'line' => 31,
        'original' => 'public function getRoles(): string',
        'fixed' => 'public function getRoles(): array'
    ],
    [
        'file' => 'src/Utils/Logger.php',
        'line' => 21,
        'original' => 'if (DEBUG_MODE) {',
        'fixed' => 'if (!defined(\'DEBUG_MODE\')) { define(\'DEBUG_MODE\', false); } if (DEBUG_MODE) {'
    ]
];

// Step 3: Apply the fixes
echo "Step 3: 修正を適用します...\n";
foreach ($mockFixes as $fix) {
    $filePath = $projectPath . '/' . $fix['file'];
    $content = file_get_contents($filePath);
    $content = str_replace($fix['original'], $fix['fixed'], $content);
    file_put_contents($filePath, $content);
    echo "Fixed {$fix['file']} line {$fix['line']}\n";
}

// Step 4: Run PHPStan again to verify fixes
echo "\nStep 4: 修正後にPHPStanを再実行して検証します...\n";
exec($cmd, $output2, $returnCode2);
echo implode("\n", $output2) . "\n";

echo "\nDemo completed successfully!\n";

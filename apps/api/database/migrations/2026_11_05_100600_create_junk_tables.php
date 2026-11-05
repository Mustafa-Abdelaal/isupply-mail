<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Junk filtering (R-23). Sender rules: block (always junk), allow (never junk), images (load remote
 * content). Junk tokens store keyed 64-bit hashes of words, never the words themselves.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('sender_rules', function (Blueprint $table) {
            $table->ulid('id')->primary();
            $table->foreignUlid('account_id')->constrained('mail_accounts')->cascadeOnDelete();
            $table->string('pattern');
            $table->string('kind', 16);
            $table->timestampsTz();

            $table->unique(['account_id', 'pattern', 'kind']);
        });

        Schema::create('junk_tokens', function (Blueprint $table) {
            $table->foreignUlid('account_id')->constrained('mail_accounts')->cascadeOnDelete();
            $table->bigInteger('token_hash');
            $table->unsignedInteger('spam_count')->default(0);
            $table->unsignedInteger('ham_count')->default(0);

            $table->primary(['account_id', 'token_hash']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('junk_tokens');
        Schema::dropIfExists('sender_rules');
    }
};

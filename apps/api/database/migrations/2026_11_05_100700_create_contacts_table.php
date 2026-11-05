<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Addresses the user has written to or heard from, for recipient autocomplete (R-17 "recent recipients").
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('contacts', function (Blueprint $table) {
            $table->ulid('id')->primary();
            $table->foreignUlid('account_id')->constrained('mail_accounts')->cascadeOnDelete();
            $table->string('email');
            $table->string('name')->nullable();
            $table->unsignedInteger('sent_count')->default(0);
            $table->unsignedInteger('received_count')->default(0);
            $table->timestampTz('last_contacted_at')->nullable();
            $table->timestampsTz();

            $table->unique(['account_id', 'email']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('contacts');
    }
};

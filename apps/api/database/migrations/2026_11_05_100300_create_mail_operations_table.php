<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * The operation log (ADR-0004): every mutation the user makes, applied to IMAP in creation order
 * per account. Microsecond timestamps keep the order stable within one request.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('mail_operations', function (Blueprint $table) {
            $table->ulid('id')->primary();
            $table->foreignUlid('account_id')->constrained('mail_accounts')->cascadeOnDelete();
            $table->string('type', 32);
            $table->jsonb('payload');
            $table->string('status', 16)->default('pending');
            $table->unsignedSmallInteger('attempts')->default(0);
            $table->text('last_error')->nullable();
            $table->timestampTz('available_at', 6);
            $table->timestampTz('completed_at')->nullable();
            $table->timestampsTz(6);

            $table->index(['account_id', 'status', 'created_at']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('mail_operations');
    }
};

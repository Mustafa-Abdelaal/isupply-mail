<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * One mailbox the backend syncs. Server settings are copied from provisioning at sign-in, so an
 * account keeps working if provisioning changes later, and shared mailboxes (R-16) fit the same table.
 * `credentials` holds only ciphertext (CredentialCipher, ADR-0005).
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('mail_accounts', function (Blueprint $table) {
            $table->ulid('id')->primary();
            $table->foreignUlid('user_id')->constrained()->cascadeOnDelete();
            $table->string('email')->unique();
            $table->string('display_name')->nullable();
            $table->string('username');
            $table->text('credentials')->nullable();
            $table->string('imap_host');
            $table->unsignedInteger('imap_port');
            $table->string('imap_encryption', 16);
            $table->string('smtp_host');
            $table->unsignedInteger('smtp_port');
            $table->string('smtp_encryption', 16);
            $table->string('status', 24)->default('active');
            $table->jsonb('capabilities')->nullable();
            $table->string('delimiter', 4)->nullable();
            $table->text('signature_html')->nullable();
            $table->unsignedInteger('junk_spam_trained')->default(0);
            $table->unsignedInteger('junk_ham_trained')->default(0);
            $table->timestampTz('last_synced_at')->nullable();
            $table->string('last_error')->nullable();
            $table->timestampTz('last_error_at')->nullable();
            $table->timestampsTz();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('mail_accounts');
    }
};

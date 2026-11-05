<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * IMAP mailboxes. `remote_name` is the name on the wire (modified UTF-7) and is what commands use;
 * `path` and `name` are decoded for display. `uidvalidity` scopes every UID stored for the folder.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('mail_folders', function (Blueprint $table) {
            $table->ulid('id')->primary();
            $table->foreignUlid('account_id')->constrained('mail_accounts')->cascadeOnDelete();
            $table->ulid('parent_id')->nullable()->index();
            $table->text('remote_name');
            $table->text('path');
            $table->text('name');
            $table->string('delimiter', 4)->nullable();
            $table->string('role', 16)->nullable();
            $table->jsonb('attributes')->nullable();
            $table->boolean('is_selectable')->default(true);
            $table->bigInteger('uidvalidity')->nullable();
            $table->bigInteger('uidnext')->nullable();
            $table->bigInteger('highestmodseq')->nullable();
            $table->unsignedInteger('total_count')->default(0);
            $table->unsignedInteger('unread_count')->default(0);
            $table->bigInteger('synced_min_uid')->nullable();
            $table->boolean('backfill_complete')->default(false);
            $table->timestampTz('last_synced_at')->nullable();
            $table->timestampTz('last_flags_synced_at')->nullable();
            $table->timestampTz('last_expunge_check_at')->nullable();
            $table->timestampsTz();

            $table->unique(['account_id', 'remote_name']);
            $table->index(['account_id', 'role']);
        });

        // Self-reference added after the table (and its primary key) exist.
        Schema::table('mail_folders', function (Blueprint $table) {
            $table->foreign('parent_id')->references('id')->on('mail_folders')->nullOnDelete();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('mail_folders');
    }
};

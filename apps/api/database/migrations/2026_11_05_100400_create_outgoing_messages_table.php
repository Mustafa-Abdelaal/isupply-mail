<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Drafts and the outbox in one table: a row is a draft until it is sent, then queued (inside the
 * undo window), sending, sent, failed or unknown (timeout after DATA: never resent automatically).
 * `message_id_header` is fixed at creation so a send can be found in Sent after an unknown outcome.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('outgoing_messages', function (Blueprint $table) {
            $table->ulid('id')->primary();
            $table->foreignUlid('account_id')->constrained('mail_accounts')->cascadeOnDelete();
            $table->string('status', 16)->default('draft');
            $table->jsonb('to_list')->nullable();
            $table->jsonb('cc_list')->nullable();
            $table->jsonb('bcc_list')->nullable();
            $table->text('subject')->nullable();
            $table->longText('html_body')->nullable();
            $table->longText('text_body')->nullable();
            $table->foreignUlid('source_message_id')->nullable()->constrained('messages')->nullOnDelete();
            $table->string('compose_mode', 16)->default('new');
            $table->text('in_reply_to_header')->nullable();
            $table->text('references_header')->nullable();
            $table->string('message_id_header');
            $table->jsonb('attachments')->nullable();
            $table->timestampTz('send_at')->nullable();
            $table->timestampTz('sent_at')->nullable();
            $table->unsignedSmallInteger('attempts')->default(0);
            $table->text('error')->nullable();
            $table->bigInteger('draft_uid')->nullable();
            $table->bigInteger('draft_uidvalidity')->nullable();
            $table->timestampTz('draft_synced_at')->nullable();
            $table->timestampsTz();

            $table->index(['account_id', 'status']);
        });

        Schema::create('uploads', function (Blueprint $table) {
            $table->ulid('id')->primary();
            $table->foreignUlid('user_id')->constrained()->cascadeOnDelete();
            $table->string('filename');
            $table->string('content_type');
            $table->unsignedBigInteger('size');
            $table->string('path');
            $table->timestampsTz();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('uploads');
        Schema::dropIfExists('outgoing_messages');
    }
};

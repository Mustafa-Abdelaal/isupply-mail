<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Where to send content-free new-mail pushes: a Web Push endpoint (+ keys), an FCM token (Android)
 * or an APNs token (iOS). Removed when the device signs out or the push service says it's gone.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('push_subscriptions', function (Blueprint $table) {
            $table->ulid('id')->primary();
            $table->foreignUlid('user_id')->constrained()->cascadeOnDelete();
            $table->string('platform', 16);
            $table->text('token');
            $table->jsonb('keys')->nullable();
            $table->string('device_name')->nullable();
            $table->unsignedBigInteger('access_token_id')->nullable()->index();
            $table->timestampTz('last_used_at')->nullable();
            $table->timestampsTz();

            $table->unique(['platform', 'token']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('push_subscriptions');
    }
};

# Product vision

## The problem

iSupply staff have `@isupply.com` mailboxes, but using them is painful. Setting up Outlook (or the
phone's mail app) means typing server names, ports and security settings. Staff get them wrong, IT
spends time on every new hire and every new phone, and some people give up and forward work mail to
personal accounts. That last habit is a security and compliance problem.

## The product

**iSupply Mail** is one app, on every device staff use, that knows the company's email setup:

- **Zero configuration**: type your work address and password, and you're in. Servers, folders,
  signature and security settings are provisioned centrally.
- **Everywhere**: web, Windows, macOS, Linux, Android and iOS, with the same features and a familiar
  experience on each.
- **Built for how iSupply works**: Arabic and English (RTL done properly), company signatures, shared
  mailboxes, and fast search across years of supplier and customer mail.
- **Safe by default**: phishing and tracking protections on, credentials kept in the device's secure
  storage, and nothing sensitive leaving the device unnecessarily.

## Who it's for

| Persona | Needs |
|---|---|
| Field and sales staff (mostly mobile) | Reliable notifications, quick replies, attachments (quotes, invoices), offline reading |
| Office staff (desktop and web) | Fast triage of high volume, search, folders, keyboard shortcuts, multiple windows |
| Managers | Shared mailboxes, delegation, readable threads |
| IT/admin | No per-device setup, central settings, the ability to revoke access when a device is lost |

## Principles

1. **It just works.** Any setting a staff member has to understand is a bug.
2. **Never lose mail.** Drafts, sends and moves are durable and recoverable.
3. **Hostile by default.** Every message is treated as untrusted. Safety beats fidelity when they conflict.
4. **One product, six platforms.** Shared behavior, native feel, no second-class platform.
5. **Arabic is first-class**, not a translation pass at the end.

## Success measures (to confirm, see [open questions](open-questions.md))

- Time from install to first message read: **under 60 seconds** with no help from IT.
- Mail-related IT tickets drop by a target agreed with IT.
- Adoption: most staff actively using it within 3 months of launch.
- Zero incidents of credential or mail-content leakage attributable to the app.

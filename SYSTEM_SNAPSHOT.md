# System Snapshot — ERP-EDUCATIVA
**Generado**: 2026-04-15 00:02:31

## Base de Datos

### `academic`
- `academic_academicperiod` (9 registros)
- `academic_academicyear` (4 registros)
- `academic_attendance` (760 registros)
- `academic_classschedule` (144 registros)
- `academic_course` (17 registros)
- `academic_enrollment` (82 registros)
- `academic_evaluationcategory` (806 registros)
- `academic_grade` (1802 registros)
- `academic_observation` (4 registros)
- `academic_subject` (108 registros)

### `accounting`
- `accounting_account` (132 registros)
- `accounting_accountingconfig` (7 registros)
- `accounting_bank` (3 registros)
- `accounting_bankaccount` (3 registros)
- `accounting_depreciation` (1 registros)
- `accounting_fiscalyear` (1 registros)
- `accounting_fixedasset` (2 registros)
- `accounting_journalentry` (45 registros)
- `accounting_journalitem` (97 registros)

### `ai`
- `ai_aiproviderconfig` (0 registros)

### `communication`
- `communication_holiday` (3 registros)
- `communication_message` (4 registros)
- `communication_notice` (8 registros)
- `communication_notice_target_students` (0 registros)
- `communication_notification` (7 registros)

### `health`
- `health_alertrule` (1 registros)
- `health_behaviorcase` (10 registros)
- `health_behaviorcase_behavior_records` (0 registros)
- `health_behaviorrecord` (45 registros)
- `health_casefollowup` (10 registros)
- `health_decerecord` (2 registros)
- `health_decevisit` (2 registros)
- `health_medicalrecord` (2 registros)
- `health_medicalvisit` (2 registros)
- `health_studentriskprofile` (6 registros)

### `helpdesk`
- `helpdesk_passstep` (0 registros)
- `helpdesk_scheduledjob` (0 registros)
- `helpdesk_servicecatalog` (2 registros)
- `helpdesk_ticket` (2 registros)
- `helpdesk_ticketattachment` (0 registros)
- `helpdesk_ticketcomment` (0 registros)
- `helpdesk_ticketsurvey` (0 registros)
- `helpdesk_workflow` (0 registros)

### `knowledge`
- `knowledge_knowledgearticle` (1 registros)
- `knowledge_knowledgecategory` (1 registros)

### `learning`
- `learning_answersubmission` (0 registros)
- `learning_assignment` (9 registros)
- `learning_assignmentsubmission` (8 registros)
- `learning_choice` (0 registros)
- `learning_coursegroup` (5 registros)
- `learning_coursetag` (19 registros)
- `learning_discussioncomment` (1 registros)
- `learning_discussionthread` (1 registros)
- `learning_learningresource` (0 registros)
- `learning_lesson` (23 registros)
- `learning_lessonprogress` (5 registros)
- `learning_lmscourse` (84 registros)
- `learning_lmsenrollment` (383 registros)
- `learning_module` (17 registros)
- `learning_question` (0 registros)
- `learning_quiz` (5 registros)
- `learning_quizattempt` (0 registros)

### `payments`
- `payments_paymentgatewayconfig` (2 registros)
- `payments_paymentlog` (11 registros)
- `payments_transaction` (12 registros)

### `privacy`
- `privacy_arcorequest` (1 registros)
- `privacy_consentrecord` (0 registros)
- `privacy_databreach` (0 registros)
- `privacy_databreach_affected_users` (0 registros)
- `privacy_policyversion` (0 registros)
- `privacy_treatmentactivity` (0 registros)

### `procedures`
- `procedures_proceduretemplate` (4 registros)
- `procedures_studentrequest` (5 registros)

### `purchases`
- `purchases_purchasecreditnote` (1 registros)
- `purchases_purchasedebitnote` (1 registros)
- `purchases_purchaseinvoice` (8 registros)
- `purchases_purchaseitem` (9 registros)
- `purchases_purchaseliquidation` (0 registros)
- `purchases_purchaseliquidationitem` (0 registros)
- `purchases_supplier` (5 registros)
- `purchases_withholding` (0 registros)

### `treasury`
- `treasury_charge` (17 registros)
- `treasury_creditnote` (0 registros)
- `treasury_debitnote` (0 registros)
- `treasury_invoice` (22 registros)
- `treasury_invoicedetail` (22 registros)
- `treasury_payment` (12 registros)
- `treasury_paymentconcept` (9 registros)
- `treasury_paymentmethod` (3 registros)
- `treasury_studentaccount` (4 registros)

### `users`
- `users_institution` (2 registros)
- `users_user` (105 registros)
- `users_user_children` (0 registros)
- `users_user_groups` (0 registros)
- `users_user_user_permissions` (0 registros)

## Endpoints API

- `/api/academic/`
- `/api/academic/<drf_format_suffix:format>`
- `/api/academic/^academic-periods/$`
- `/api/academic/^academic-periods/(?P<pk>[^/.]+)/$`
- `/api/academic/^academic-years/$`
- `/api/academic/^academic-years/(?P<pk>[^/.]+)/$`
- `/api/academic/^academic-years/(?P<pk>[^/.]+)/set_active/$`
- `/api/academic/^attendance/$`
- `/api/academic/^attendance/(?P<pk>[^/.]+)/$`
- `/api/academic/^attendance/dashboard-stats/$`
- `/api/academic/^attendance/report/$`
- `/api/academic/^courses/$`
- `/api/academic/^courses/(?P<pk>[^/.]+)/$`
- `/api/academic/^enrollments/$`
- `/api/academic/^enrollments/(?P<pk>[^/.]+)/$`
- `/api/academic/^enrollments/(?P<pk>[^/.]+)/behavioral-summary/$`
- `/api/academic/^enrollments/(?P<pk>[^/.]+)/download_report_card/$`
- `/api/academic/^enrollments/excellence-ranking/$`
- `/api/academic/^enrollments/institution-stats/$`
- `/api/academic/^evaluation-categories/$`
- `/api/academic/^evaluation-categories/(?P<pk>[^/.]+)/$`
- `/api/academic/^grades/$`
- `/api/academic/^grades/(?P<pk>[^/.]+)/$`
- `/api/academic/^grades/course-stats/$`
- `/api/academic/^observations/$`
- `/api/academic/^observations/(?P<pk>[^/.]+)/$`
- `/api/academic/^schedules/$`
- `/api/academic/^schedules/(?P<pk>[^/.]+)/$`
- `/api/academic/^subjects/$`
- `/api/academic/^subjects/(?P<pk>[^/.]+)/$`
- `/api/accounting/`
- `/api/accounting/<drf_format_suffix:format>`
- `/api/accounting/^accounts/$`
- `/api/accounting/^accounts/(?P<pk>[^/.]+)/$`
- `/api/accounting/^bank-accounts/$`
- `/api/accounting/^bank-accounts/(?P<pk>[^/.]+)/$`
- `/api/accounting/^banks/$`
- `/api/accounting/^banks/(?P<pk>[^/.]+)/$`
- `/api/accounting/^entries/$`
- `/api/accounting/^entries/(?P<pk>[^/.]+)/$`
- `/api/accounting/^entries/(?P<pk>[^/.]+)/cancel_entry/$`
- `/api/accounting/^entries/(?P<pk>[^/.]+)/post_entry/$`
- `/api/accounting/^fiscal-years/$`
- `/api/accounting/^fiscal-years/(?P<pk>[^/.]+)/$`
- `/api/accounting/^fiscal-years/(?P<pk>[^/.]+)/close_year/$`
- `/api/accounting/^fixed-assets/$`
- `/api/accounting/^fixed-assets/(?P<pk>[^/.]+)/$`
- `/api/accounting/^fixed-assets/(?P<pk>[^/.]+)/calculate_depreciation/$`
- `/api/accounting/^reports/$`
- `/api/accounting/^reports/ats/$`
- `/api/accounting/^reports/balance_sheet/$`
- `/api/accounting/^reports/income_statement/$`
- `/api/accounting/^reports/ledger/$`
- `/api/ai/`
- `/api/ai/<drf_format_suffix:format>`
- `/api/ai/^assistant/ask/$`
- `/api/ai/^assistant/summarize/$`
- `/api/ai/^config/$`
- `/api/ai/^config/(?P<pk>[^/.]+)/$`
- `/api/ai/^config/test_connection/$`
- `/api/auth/refresh/`
- `/api/communication/`
- `/api/communication/<drf_format_suffix:format>`
- `/api/communication/^holidays/$`
- `/api/communication/^holidays/(?P<pk>[^/.]+)/$`
- `/api/communication/^holidays/populate_holidays/$`
- `/api/communication/^messages/$`
- `/api/communication/^messages/(?P<pk>[^/.]+)/$`
- `/api/communication/^messages/inbox/$`
- `/api/communication/^messages/sent/$`
- `/api/communication/^notices/$`
- `/api/communication/^notices/(?P<pk>[^/.]+)/$`
- `/api/communication/^notifications/$`
- `/api/communication/^notifications/(?P<pk>[^/.]+)/$`
- `/api/communication/^notifications/(?P<pk>[^/.]+)/mark_read/$`
- `/api/health/`
- `/api/health/<drf_format_suffix:format>`
- `/api/health/^alert-rules/$`
- `/api/health/^alert-rules/(?P<pk>[^/.]+)/$`
- `/api/health/^behavior-cases/$`
- `/api/health/^behavior-cases/(?P<pk>[^/.]+)/$`
- `/api/health/^behavior-cases/(?P<pk>[^/.]+)/close/$`
- `/api/health/^behavior-cases/(?P<pk>[^/.]+)/derive/$`
- `/api/health/^behavior-cases/(?P<pk>[^/.]+)/reopen/$`
- `/api/health/^behavior-records/$`
- `/api/health/^behavior-records/(?P<pk>[^/.]+)/$`
- `/api/health/^behavior-records/by-student/$`
- `/api/health/^behavior-records/quick-create/$`
- `/api/health/^case-follow-ups/$`
- `/api/health/^case-follow-ups/(?P<pk>[^/.]+)/$`
- `/api/health/^dece-records/$`
- `/api/health/^dece-records/(?P<pk>[^/.]+)/$`
- `/api/health/^dece-visits/$`
- `/api/health/^dece-visits/(?P<pk>[^/.]+)/$`
- `/api/health/^medical-records/$`
- `/api/health/^medical-records/(?P<pk>[^/.]+)/$`
- `/api/health/^medical-visits/$`
- `/api/health/^medical-visits/(?P<pk>[^/.]+)/$`
- `/api/health/^student-risk-profiles/$`
- `/api/health/^student-risk-profiles/(?P<pk>[^/.]+)/$`
- `/api/health/^student-risk-profiles/critical-alerts/$`
- `/api/health/^student-risk-profiles/dashboard-stats/$`
- `/api/health/^student-risk-profiles/recalculate-all/$`
- `/api/helpdesk/`
- `/api/helpdesk/<drf_format_suffix:format>`
- `/api/helpdesk/^attachments/$`
- `/api/helpdesk/^attachments/(?P<pk>[^/.]+)/$`
- `/api/helpdesk/^catalog/$`
- `/api/helpdesk/^catalog/(?P<pk>[^/.]+)/$`
- `/api/helpdesk/^comments/$`
- `/api/helpdesk/^comments/(?P<pk>[^/.]+)/$`
- `/api/helpdesk/^tickets/$`
- `/api/helpdesk/^tickets/(?P<pk>[^/.]+)/$`
- `/api/helpdesk/^tickets/(?P<pk>[^/.]+)/rate/$`
- `/api/helpdesk/^tickets/(?P<pk>[^/.]+)/reopen/$`
- `/api/helpdesk/^workflows/$`
- `/api/helpdesk/^workflows/(?P<pk>[^/.]+)/$`
- `/api/knowledge/`
- `/api/knowledge/<drf_format_suffix:format>`
- `/api/knowledge/^articles/$`
- `/api/knowledge/^articles/(?P<pk>[^/.]+)/$`
- `/api/knowledge/^categories/$`
- `/api/knowledge/^categories/(?P<pk>[^/.]+)/$`
- `/api/learning/`
- `/api/learning/<drf_format_suffix:format>`
- `/api/learning/^assignments/$`
- `/api/learning/^assignments/(?P<pk>[^/.]+)/$`
- `/api/learning/^choices/$`
- `/api/learning/^choices/(?P<pk>[^/.]+)/$`
- `/api/learning/^courses/$`
- `/api/learning/^courses/(?P<pk>[^/.]+)/$`
- `/api/learning/^courses/(?P<pk>[^/.]+)/enroll/$`
- `/api/learning/^courses/(?P<pk>[^/.]+)/sync_students/$`
- `/api/learning/^discussion-comments/$`
- `/api/learning/^discussion-comments/(?P<pk>[^/.]+)/$`
- `/api/learning/^discussion-threads/$`
- `/api/learning/^discussion-threads/(?P<pk>[^/.]+)/$`
- `/api/learning/^enrollments/$`
- `/api/learning/^enrollments/(?P<pk>[^/.]+)/$`
- `/api/learning/^groups/$`
- `/api/learning/^groups/(?P<pk>[^/.]+)/$`
- `/api/learning/^lessons/$`
- `/api/learning/^lessons/(?P<pk>[^/.]+)/$`
- `/api/learning/^lessons/(?P<pk>[^/.]+)/complete/$`
- `/api/learning/^modules/$`
- `/api/learning/^modules/(?P<pk>[^/.]+)/$`
- `/api/learning/^progress/$`
- `/api/learning/^progress/(?P<pk>[^/.]+)/$`
- `/api/learning/^questions/$`
- `/api/learning/^questions/(?P<pk>[^/.]+)/$`
- `/api/learning/^quiz-attempts/$`
- `/api/learning/^quiz-attempts/(?P<pk>[^/.]+)/$`
- `/api/learning/^quiz-attempts/(?P<pk>[^/.]+)/submit_answers/$`
- `/api/learning/^quizzes/$`
- `/api/learning/^quizzes/(?P<pk>[^/.]+)/$`
- `/api/learning/^resources/$`
- `/api/learning/^resources/(?P<pk>[^/.]+)/$`
- `/api/learning/^submissions/$`
- `/api/learning/^submissions/(?P<pk>[^/.]+)/$`
- `/api/learning/^tags/$`
- `/api/learning/^tags/(?P<pk>[^/.]+)/$`
- `/api/learning/calendar/events/`
- `/api/learning/instructor/export/`
- `/api/learning/instructor/stats/`
- `/api/learning/instructor/submissions/`
- `/api/maintenance/backup/`
- `/api/maintenance/log/`
- `/api/maintenance/reset/`
- `/api/maintenance/restore/`
- `/api/maintenance/users/`
- `/api/payments/`
- `/api/payments/<drf_format_suffix:format>`
- `/api/payments/^$`
- `/api/payments/^(?P<pk>[^/.]+)/$`
- `/api/payments/^(?P<pk>[^/.]+)/delete_transfer/$`
- `/api/payments/^(?P<pk>[^/.]+)/verify_transfer/$`
- `/api/payments/^checkout/$`
- `/api/payments/^config/$`
- `/api/payments/^config/(?P<pk>[^/.]+)/$`
- `/api/payments/^payment-gateway-configs/$`
- `/api/payments/^payment-gateway-configs/(?P<pk>[^/.]+)/$`
- `/api/payments/^pending_transfers/$`
- `/api/payments/webhook/<str:gateway_name>/`
- `/api/privacy/`
- `/api/privacy/<drf_format_suffix:format>`
- `/api/privacy/^arco/$`
- `/api/privacy/^arco/(?P<pk>[^/.]+)/$`
- `/api/privacy/^breaches/$`
- `/api/privacy/^breaches/(?P<pk>[^/.]+)/$`
- `/api/privacy/^consents/$`
- `/api/privacy/^consents/(?P<pk>[^/.]+)/$`
- `/api/privacy/^policies/$`
- `/api/privacy/^policies/(?P<pk>[^/.]+)/$`
- `/api/privacy/^rat/$`
- `/api/privacy/^rat/(?P<pk>[^/.]+)/$`
- `/api/procedures/`
- `/api/procedures/<drf_format_suffix:format>`
- `/api/procedures/^requests/$`
- `/api/procedures/^requests/(?P<pk>[^/.]+)/$`
- `/api/procedures/^requests/(?P<pk>[^/.]+)/resolve/$`
- `/api/procedures/^templates/$`
- `/api/procedures/^templates/(?P<pk>[^/.]+)/$`
- `/api/purchases/`
- `/api/purchases/<drf_format_suffix:format>`
- `/api/purchases/^credit-notes/$`
- `/api/purchases/^credit-notes/(?P<pk>[^/.]+)/$`
- `/api/purchases/^debit-notes/$`
- `/api/purchases/^debit-notes/(?P<pk>[^/.]+)/$`
- `/api/purchases/^invoices/$`
- `/api/purchases/^invoices/(?P<pk>[^/.]+)/$`
- `/api/purchases/^invoices/(?P<pk>[^/.]+)/cancel/$`
- `/api/purchases/^invoices/(?P<pk>[^/.]+)/validate/$`
- `/api/purchases/^liquidations/$`
- `/api/purchases/^liquidations/(?P<pk>[^/.]+)/$`
- `/api/purchases/^liquidations/(?P<pk>[^/.]+)/cancel/$`
- `/api/purchases/^liquidations/(?P<pk>[^/.]+)/validate/$`
- `/api/purchases/^suppliers/$`
- `/api/purchases/^suppliers/(?P<pk>[^/.]+)/$`
- `/api/token/`
- `/api/treasury/`
- `/api/treasury/<drf_format_suffix:format>`
- `/api/treasury/^accounts/$`
- `/api/treasury/^accounts/(?P<pk>[^/.]+)/$`
- `/api/treasury/^charges/$`
- `/api/treasury/^charges/(?P<pk>[^/.]+)/$`
- `/api/treasury/^charges/financial-stats/$`
- `/api/treasury/^charges/generate-monthly/$`
- `/api/treasury/^concepts/$`
- `/api/treasury/^concepts/(?P<pk>[^/.]+)/$`
- `/api/treasury/^credit-notes/$`
- `/api/treasury/^credit-notes/(?P<pk>[^/.]+)/$`
- `/api/treasury/^debit-notes/$`
- `/api/treasury/^debit-notes/(?P<pk>[^/.]+)/$`
- `/api/treasury/^invoices/$`
- `/api/treasury/^invoices/(?P<pk>[^/.]+)/$`
- `/api/treasury/^invoices/(?P<pk>[^/.]+)/download_pdf/$`
- `/api/treasury/^invoices/(?P<pk>[^/.]+)/download_xml/$`
- `/api/treasury/^invoices/(?P<pk>[^/.]+)/send-sri/$`
- `/api/treasury/^invoices/mass-billing/$`
- `/api/treasury/^invoices/process-payment/$`
- `/api/treasury/^methods/$`
- `/api/treasury/^methods/(?P<pk>[^/.]+)/$`
- `/api/users/`
- `/api/users/<drf_format_suffix:format>`
- `/api/users/^$`
- `/api/users/^(?P<pk>[^/.]+)/$`
- `/api/users/^institutions/$`
- `/api/users/^institutions/(?P<pk>[^/.]+)/$`

## Estado de Migraciones

✅ Todas las migraciones están aplicadas.

## Usuarios por Rol

- **ACCOUNTANT**: 1 usuarios
- **ADMIN**: 1 usuarios
- **DECE**: 1 usuarios
- **LOCAL_ADMIN**: 1 usuarios
- **RECTOR**: 1 usuarios
- **STUDENT**: 83 usuarios
- **TEACHER**: 17 usuarios

## Estado LMS

- Grupos: 5
- Etiquetas: 19
- Cursos LMS: 84
- Cursos sin etiqueta: 21

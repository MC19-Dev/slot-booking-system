# football_booking

```mermaid
flowchart TD
    A[Start: validate_config] --> B[Calculate Target Date/Time]
    B --> C[Stage 1: Main Account]
    C --> D[Login sportinclujnapoca.ro]
    D --> E[Navigate to Football Pitch]
    E --> F[Select Day & Time Slot]
    F --> G[Submit Initial Reservation]
    G --> H[Extract Confirmation Link]

    H --> I[Stage 2: Friend Accounts]
    I --> J{More Accounts?}
    J -- Yes --> K[Login Friend Account]
    K --> L[Access Shared Confirmation Link]
    L --> M[Confirm Participation]
    M --> J

    J -- No --> N[Finish: Reservation Confirmed]
```
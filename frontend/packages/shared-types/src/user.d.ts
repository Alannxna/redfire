export interface User {
    id: string;
    username: string;
    email: string;
    role: 'user' | 'admin' | 'trader';
    status: 'active' | 'inactive' | 'suspended';
    createdAt: Date;
    updatedAt: Date;
}
export interface UserProfile {
    userId: string;
    firstName?: string;
    lastName?: string;
    phone?: string;
    avatar?: string;
    preferences: UserPreferences;
}
export interface UserPreferences {
    theme: 'light' | 'dark' | 'auto';
    language: string;
    timezone: string;
    notifications: NotificationSettings;
}
export interface NotificationSettings {
    email: boolean;
    push: boolean;
    sms: boolean;
    tradingAlerts: boolean;
    systemUpdates: boolean;
}
//# sourceMappingURL=user.d.ts.map
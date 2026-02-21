// AI Ustoz — API Configuration
// Railway backend URL — deploy qilgandan keyin shu yerga o'z URL ingizni yozing
const API_BASE = 'https://ai-ustozz-production.up.railway.app';

// WebSocket URL (wss:// HTTPS uchun)
const WS_BASE = API_BASE.replace('https://', 'wss://').replace('http://', 'ws://');

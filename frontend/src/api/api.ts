import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000', 
});

// Отправка номера телефона
export const sendCode = async (phone: string) => {
  const response = await API.post('/send-code', { phone });
  return response.data;
};

// Подтверждение кода (с поддержкой 2FA пароля, если нужно)
export const verifyCode = async (
  phone: string,
  code: string,
  password?: string
) => {
  const response = await API.post('/verify-code', {
    phone,
    code,
    password,
  });
  return response.data;
};

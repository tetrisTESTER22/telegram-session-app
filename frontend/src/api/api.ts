import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000', 
});

export const sendCode = async (phone: string) => {
  const response = await API.post('/send-code', { phone });
  return response.data;
};

export const verifyCode = async (phone: string, code: string) => {
  const response = await API.post('/verify-code', { phone, code });
  return response.data;
};

import { useState } from 'react';
import { verifyCode } from '../api/api';

type EnterCodeProps = {
  phone: string;
  onCodeVerified: (code: string) => void;
  on2FARequired: () => void;
};

function EnterCode({ phone, onCodeVerified, on2FARequired }: EnterCodeProps) {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setStatus('');
    setLoading(true);

    try {
      const res = await verifyCode(phone, code);
      if (res.status === 'authorized') {
        setStatus(`✅ Успішно авторизовано як @${res.username || 'користувач'}`);
      }
    } catch (err: any) {
      if (err.response?.status === 401) {
        // Включена двухфакторка — просим пароль
        onCodeVerified(code); // сохраняем код
        on2FARequired();      // переходим на экран 2FA
      } else {
        setError('❌ Неправильний код або помилка авторизації.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Введіть код із Telegram</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Код з SMS"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Перевірка...' : 'Підтвердити'}
        </button>
      </form>

      {status && <p style={{ color: 'green' }}>{status}</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
}

export default EnterCode;

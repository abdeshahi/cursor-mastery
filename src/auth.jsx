import { useState } from 'react'
import { Eye, EyeOff, LockKeyhole, LogIn, ShieldCheck, Smartphone } from 'lucide-react'

export function LoginScreen({ signIn, demoSignIn, online }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [role, setRole] = useState('admin')
  const [showPassword, setShowPassword] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    if (!online) {
      demoSignIn({ fullName: name, role })
      return
    }
    setSubmitting(true)
    const result = await signIn({ email, password })
    if (result.error) setError('ایمیل یا رمز عبور صحیح نیست.')
    setSubmitting(false)
  }

  return (
    <main className="login-page">
      <section className="login-showcase">
        <div className="login-brand">
          <div className="login-logo"><Smartphone size={28} /></div>
          <div><strong>سی‌تی‌تل</strong><span>مدیریت هوشمند فروشگاه</span></div>
        </div>
        <div className="showcase-copy">
          <span><ShieldCheck size={17} /> محیط امن پرسنل</span>
          <h1>فروشگاه، همیشه<br />همراه تیم شماست.</h1>
          <p>فروش، موجودی و تعمیرات را از هر دستگاهی مدیریت کنید.</p>
        </div>
        <div className="phone-preview">
          <div className="phone-notch" />
          <div className="preview-header"><span>امروز</span><strong>۴۸٫۳ میلیون</strong></div>
          <div className="preview-chart"><i /><i /><i /><i /><i /><i /></div>
          <div className="preview-row"><span /><div><strong>فروش جدید</strong><small>همین حالا</small></div><b>+</b></div>
          <div className="preview-row"><span /><div><strong>موجودی به‌روز شد</strong><small>۲ دقیقه پیش</small></div><b>✓</b></div>
        </div>
      </section>
      <section className="login-form-side">
        <div className="login-card">
          <div className="mobile-login-brand"><div className="login-logo"><Smartphone size={23} /></div><strong>سی‌تی‌تل</strong></div>
          <div className="login-heading">
            <span className={`connection-badge ${online ? 'online' : ''}`}><i />{online ? 'متصل به دیتابیس مرکزی' : 'حالت نمایشی این دستگاه'}</span>
            <h2>ورود به پنل پرسنل</h2>
            <p>{online ? 'با حساب سازمانی خود وارد شوید.' : 'برای مشاهده نسخه نمایشی، نام و نقش خود را انتخاب کنید.'}</p>
          </div>
          <form className="login-form" onSubmit={submit}>
            {online ? (
              <>
                <label><span>ایمیل کاری</span><input dir="ltr" type="email" required autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="staff@cttel.ir" /></label>
                <label><span>رمز عبور</span><div className="password-input"><input dir="ltr" type={showPassword ? 'text' : 'password'} required autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="••••••••" /><button type="button" onClick={() => setShowPassword((value) => !value)}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div></label>
              </>
            ) : (
              <>
                <label><span>نام و نام خانوادگی</span><input required value={name} onChange={(event) => setName(event.target.value)} placeholder="مثلاً محمد رضایی" /></label>
                <label><span>نقش در فروشگاه</span><select value={role} onChange={(event) => setRole(event.target.value)}><option value="admin">مدیر فروشگاه</option><option value="sales">فروشنده</option><option value="technician">تعمیرکار</option></select></label>
              </>
            )}
            {error && <div className="login-error">{error}</div>}
            <button className="login-submit" disabled={submitting}><LogIn size={18} />{submitting ? 'در حال ورود...' : 'ورود به فروشگاه'}</button>
          </form>
          <div className="login-security"><LockKeyhole size={15} /><span>اطلاعات ورود و داده‌های فروشگاه به‌صورت امن نگهداری می‌شوند.</span></div>
        </div>
      </section>
    </main>
  )
}

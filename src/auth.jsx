import { useEffect, useState } from 'react'
import { Eye, EyeOff, LockKeyhole, LogIn, ShieldCheck, Smartphone } from 'lucide-react'
import { supabase, supabaseConfigured } from './lib/supabase'

export const roleLabels = {
  admin: 'مدیر فروشگاه',
  sales: 'فروشنده',
  technician: 'تعمیرکار',
}

export function useAuth() {
  const [user, setUser] = useState(null)
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!supabaseConfigured) {
      try {
        const saved = JSON.parse(localStorage.getItem('cttel-demo-user'))
        if (saved) {
          setUser({ id: 'demo-user', email: 'demo@cttel.local' })
          setProfile(saved)
        }
      } catch {
        localStorage.removeItem('cttel-demo-user')
      }
      setLoading(false)
      return undefined
    }

    const loadProfile = async (sessionUser) => {
      if (!sessionUser) {
        setUser(null)
        setProfile(null)
        setLoading(false)
        return
      }
      setUser(sessionUser)
      const { data } = await supabase
        .from('profiles')
        .select('id, full_name, role')
        .eq('id', sessionUser.id)
        .maybeSingle()
      setProfile(data || {
        id: sessionUser.id,
        full_name: sessionUser.user_metadata?.full_name || sessionUser.email,
        role: sessionUser.app_metadata?.role || 'sales',
      })
      setLoading(false)
    }

    supabase.auth.getSession().then(({ data }) => loadProfile(data.session?.user))
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      loadProfile(session?.user)
    })
    return () => listener.subscription.unsubscribe()
  }, [])

  const signIn = async ({ email, password }) => {
    if (!supabaseConfigured) return { error: new Error('دیتابیس مرکزی تنظیم نشده است.') }
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    return { error }
  }

  const demoSignIn = ({ fullName, role }) => {
    const demoProfile = { id: 'demo-user', full_name: fullName || 'مدیر سی‌تی‌تل', role }
    localStorage.setItem('cttel-demo-user', JSON.stringify(demoProfile))
    setUser({ id: 'demo-user', email: 'demo@cttel.local' })
    setProfile(demoProfile)
  }

  const signOut = async () => {
    if (supabaseConfigured) await supabase.auth.signOut()
    localStorage.removeItem('cttel-demo-user')
    setUser(null)
    setProfile(null)
  }

  return { user, profile, loading, signIn, demoSignIn, signOut, online: supabaseConfigured }
}

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

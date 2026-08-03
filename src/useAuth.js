import { useEffect, useState } from 'react'
import { supabase, supabaseConfigured } from './lib/supabase'

export const roleLabels = {
  admin: 'مدیر فروشگاه',
  sales: 'فروشنده',
  technician: 'تعمیرکار',
}

function readDemoProfile() {
  if (supabaseConfigured) return null
  try {
    return JSON.parse(localStorage.getItem('cttel-demo-user'))
  } catch {
    localStorage.removeItem('cttel-demo-user')
    return null
  }
}

export function useAuth() {
  const [initialDemoProfile] = useState(readDemoProfile)
  const [user, setUser] = useState(() => initialDemoProfile ? { id: 'demo-user', email: 'demo@cttel.local' } : null)
  const [profile, setProfile] = useState(initialDemoProfile)
  const [loading, setLoading] = useState(supabaseConfigured)

  useEffect(() => {
    if (!supabaseConfigured) return undefined

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

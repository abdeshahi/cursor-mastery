import { useEffect, useRef, useState } from 'react'
import { supabase } from './lib/supabase'

export function useStoreData(key, fallback, userId, online) {
  const initialValue = useRef(fallback)
  const [value, setValue] = useState(() => {
    try {
      const saved = localStorage.getItem(key)
      return saved ? JSON.parse(saved) : fallback
    } catch {
      return fallback
    }
  })

  useEffect(() => {
    if (!online || !userId || !supabase) return undefined
    let active = true

    const load = async () => {
      const { data } = await supabase
        .from('store_data')
        .select('payload')
        .eq('key', key)
        .maybeSingle()

      if (!active) return
      if (data?.payload) {
        setValue(data.payload)
        localStorage.setItem(key, JSON.stringify(data.payload))
      } else {
        const localValue = (() => {
          try {
            return JSON.parse(localStorage.getItem(key)) || initialValue.current
          } catch {
            return initialValue.current
          }
        })()
        await supabase.from('store_data').upsert({
          key,
          payload: localValue,
          updated_by: userId,
          updated_at: new Date().toISOString(),
        })
      }
    }

    load()
    const channel = supabase
      .channel(`store-data-${key}`)
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'store_data', filter: `key=eq.${key}` },
        (event) => {
          if (!event.new?.payload) return
          setValue(event.new.payload)
          localStorage.setItem(key, JSON.stringify(event.new.payload))
        },
      )
      .subscribe()

    return () => {
      active = false
      supabase.removeChannel(channel)
    }
  }, [key, online, userId])

  const update = (next) => {
    setValue((current) => {
      const result = typeof next === 'function' ? next(current) : next
      localStorage.setItem(key, JSON.stringify(result))
      if (online && userId && supabase) {
        supabase.from('store_data').upsert({
          key,
          payload: result,
          updated_by: userId,
          updated_at: new Date().toISOString(),
        }).then(({ error }) => {
          if (error) console.error(`Sync failed for ${key}`, error.message)
        })
      }
      return result
    })
  }

  return [value, update]
}

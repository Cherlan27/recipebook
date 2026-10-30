import { describe, expect, it } from 'vitest'
import { toLines } from './toLines'

describe('toLines', () => {
  it('splits on \n', () => {
    expect(toLines('a\nb')).toEqual(['a', 'b'])
  })

  it('splits on \r\n', () => {
    expect(toLines('a\r\nb')).toEqual(['a', 'b'])
  })

  it('trims every line', () => {
    expect(toLines('  a \n\tb  ')).toEqual(['a', 'b'])
  })

  it('drops empty and whitespace-only lines', () => {
    expect(toLines('200 g Pasta\n\n1 Onion\n')).toEqual(['200 g Pasta', '1 Onion'])
    expect(toLines('Boil water\r\n  \r\nCook pasta')).toEqual(['Boil water', 'Cook pasta'])
  })

  it('returns an empty list for null', () => {
    expect(toLines(null)).toEqual([])
  })
})

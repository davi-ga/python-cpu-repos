
// Only used if there's nothing selected, but has to pass the typecheck
export const EMPTY_SPLIT_TAGS = [ [], new Map([["emoji", "X"], ["lat", 0], ["lon", 0]]) ]

export function split_normal_and_special_tags(tags, index)
{
  // tags -> normal_tags, special_attrs
  //
  // with "--special-key-value" --> special_attrs[key] = value
  // WILL ALSO FILL IN DEFAULT VALUES for emoji,lat,lon
  //
  // this is icky, but doesn't require changing the db
  // or hardcoding things in javascript
  const normal_tags = tags.split(",")
    .map((tag, index) => { return tag.trim(); })
    .filter((tag) => !tag.startsWith("--"));
  const special_tags = tags.split(",")
    .map((tag, index) => { return tag.trim(); })
    .filter((tag) => tag.startsWith("--"));

  const special_attrs = new Map();
  for (let i = 0; i < special_tags.length; i++) {
    const tag = special_tags[i];
    console.assert(tag.startsWith("--special-"), tag);
    const x = tag.replace("--special-",'').split('-')
    console.assert(x.length === 2, x.length, x);
    const key = x[0].trim(), val = x[1].trim();
    console.assert(!special_attrs.has(key), key, special_attrs);
    special_attrs.set(key, val);
  }

  /* Fallback emoji */
  if (!special_attrs.has('emoji'))
    special_attrs.set('emoji', DEFAULT_EMOJIS[index % DEFAULT_EMOJIS.length]);

  /* Fallback positon
   * This doesn't work well, should be a last resort */
  if (!special_attrs.has('lat'))
    special_attrs.set('lat', random_map_pct(index));
  if (!special_attrs.has('lon'))
    special_attrs.set('lon', random_map_pct(index+47));

  return [normal_tags, special_attrs];
}



/////// Position on the map -- just percents for now ////////////

function rnd_float(seed)
{
    /* from v8 -- Robert Jenkins' 32 bit integer hash function.
     * overkill, but all things I found are either terrible
     * (like, linear on the seed), or ten pages long */
    seed = seed & 0xffffffff
    seed = (seed + 0x7ed55d16 + (seed << 12)) & 0xffffffff
    seed = (seed ^ 0xc761c23c ^ (seed >>> 19)) & 0xffffffff
    seed = (seed + 0x165667b1 + (seed << 5)) & 0xffffffff
    seed = ((seed + 0xd3a2646c) ^ (seed << 9)) & 0xffffffff
    seed = (seed + 0xfd7046c5 + (seed << 3)) & 0xffffffff
    seed = (seed ^ 0xb55a4f09 ^ (seed >>> 16)) & 0xffffffff
    return (seed & 0xfffffff) / 0x10000000;
}
function random_map_pct(seed)
{
    const f = rnd_float(seed);
    const i = Math.floor(f*10);
    return 5 + i*9;
}

export function get_chal_pos(special_attrs)
{
    // For now they are all percents
    console.assert(special_attrs.has('lat'), special_attrs);
    console.assert(special_attrs.has('lon'), special_attrs);
    const mtop = special_attrs.get('lat'), mleft = special_attrs.get('lon');
    return [ '' + mtop + "%", '' + mleft + "%" ];
}


const DEFAULT_EMOJIS = [
    '🤡', '👹', '👺', '👻', '👽', '👾', '🤖', '😺', '😻', '🖖',
    '🧟', '🧞', '👣', '🧳', '🧶', '🥽', '🥼', '💫', '🚌', '🚲',
    '💥', '🐩', '🐕', '🦌', '🦄', '🐹', '🦜', '🎹', '🏵️', '🌸',    
    '🌟', '🌠', '🌫️', '🔥', '✨', '🎋', '🥥', '🏝️', '🏜️', '🏖️',
    '🍇', '🍅', '🥐', '🍔', '🍟', '🍿', '🍙', '🍨', '🍩', '🍰',    
    '🍫', '🍭', '🍺', '🍽️', '🍍', '🥑', '🎪', '🎫', '⚾', '⚽',    
    '🧩', '🎲', '🎷', '🎸', '🎻', '🏹', '💈', '🎏', '🧸', '🧾',    
    '📝', '🚰', '💤', '🃏', '🀄', '🎴', 'xx', '📛', '🔱', '🌋'
];

varying vec2 v_position;
uniform vec4 color;
uniform float volume, treble, basses, time;
uniform sampler2D spectra;

#define cl(x) clamp(x, 0.0, 1.0)

float get_spectra(float p, float past){
  return texture2D(spectra, vec2(p/2.0+0.5, past)).r;
}

void main() {
  vec2 p = v_position;
  p *= 1.2;
  vec4 col = vec4(0.0);
  float l = length(p);
  float a = atan(p.y, p.x);

  float t = mod(time * 0.1, 0.1);

  float s = 1.0 - clamp(get_spectra(a / 6.28 - 0.5 + t, 0.0), 0.0, 0.5);

  col += 1.0;
  float radius_1 = (1.0 - clamp((l - 1.0)/0.01, 0.0, 1.0));
  col *= clamp((abs(l)-s)/0.01, 0.0, 1.0) * radius_1;

  float rolling = get_spectra(a / 6.28 - 0.0, (1.0-l)/4.0) * (2.0 + a * 0.1);
  rolling = pow(4.0 * rolling, 4.0);

  rolling *= 10.0 * radius_1;
  col.r += rolling;
  col.a = 0.8;

  col.r += 0.2 * volume;

  col *= 0.1;

  gl_FragColor = col;
}

#extension GL_EXT_gpu_shader4 : enable

varying vec2 v_position;
uniform vec4 color;
uniform float volume, treble, basses, time, width, height, ratio;
uniform sampler2D spectra;

#define cl(x) clamp(x, 0.0, 1.0)

float get_spectra(float p, float past){
  return texture2D(spectra, vec2(p/2.0+0.5, past)).r;
}

vec4 xor_viz(vec2 p) {
  vec4 col = vec4(0.0);

  float t = mod(time * 0.1, 0.1);
  float s = 1.0 - clamp(get_spectra(p.x - 0.5 + t, 0.0), 0.0, 0.5);


  s *= volume * 0.2 + 0.7 * (1.0 - 2.0 * length(p));

  p = cos(p);

  p *= 300.0;

  int i = int(p.x + 1e3 + s * 100.0);
  int j = int(p.y + 4.4e2 + tan(s * 2.0) * 100.0);
  int z = 0;


  for (int k = 0; k < 6; k++) {
    z += (i ^ j) & (i % j);

    z += int(s);

    if (z < 10) {
      col.rgb += 0.4;
    }

    col.b += 0.1 * (1.0 - p.x/300.0);
    col.r += 0.15 * (1.0 - p.x/300.0);
  }

  col.r += 1.0;

  return col;
}

void main() {
  vec2 p = v_position * vec2(1.0/ratio, 1.0);
  p *= 1.2;
  vec4 col = vec4(0.0);

  col += xor_viz(p);

  col *= 0.1;

  col.a = 1.0;

  gl_FragColor = col;
}


// It's still getting higher as I save

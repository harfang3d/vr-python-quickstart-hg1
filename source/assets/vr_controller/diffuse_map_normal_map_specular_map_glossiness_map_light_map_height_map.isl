in {
	tex2D diffuse_map;
	tex2D specular_map;
	tex2D glossiness_map;
	tex2D height_map;
	tex2D normal_map;
	tex2D light_map;

	float min_layer = 4;
	float max_layer = 16;

	float parallax_scale = 0.01;
}

variant {

	vertex {
		out {
			vec3 v_vtx;
			vec2 v_uv;
			vec3 v_tangent;
			vec3 v_bitangent;
			vec3 v_normal;
			mat3 v_normalmatrix;	
		}

		source %{
			v_uv = vUV0;
			v_vtx = vPosition;

			v_tangent = vTangent;
			v_bitangent = vBitangent;
			v_normal = vNormal;
			v_normalmatrix = vNormalMatrix;

			%position% = vec4(vPosition, 1.0);
		%}
	}

	pixel {

		global %{
			#include "@core/shaders/common.i"

			vec2 ParallaxOffsetUV(vec3 view_dir, vec2 _uv, float scale)
			{
				vec2 uv = _uv;
				view_dir = normalize(view_dir);

				float num_layers = mix(max_layer, min_layer, abs(view_dir.z));
				float height_step = 1.0 / num_layers;

				vec2 uv_step = view_dir.xy / view_dir.z * scale / num_layers;

				// while point is above surface
				float prv_height = 0, height = 0;
				float prv_tex_height = 0, tex_height = 0;
				
				int i = 0;
				while (true) {
					prv_tex_height = tex_height;

					tex_height = texture2D(height_map, uv).r;
					if (height >= tex_height || i >= num_layers)
						break;

					prv_height = height;
					height += height_step;
					uv += uv_step;
					i++;
				}

				// if there is no depth
				if(height <= 0.0)
					return _uv;

				// fine check
				uv -= uv_step;
				i = 0;
				while (i < 3 && abs(height - tex_height) > 1e-3) {
					float dt0 = prv_tex_height - prv_height;
					float dt1 = height - tex_height;
					float k = dt0 / (dt0 + dt1);
					vec2 new_uv = uv + uv_step * k;
					float new_height = prv_height + height_step * k;

					float new_tex_height = texture2D(height_map, new_uv).r;
					if (new_height >= new_tex_height) {
						height = new_height;
						tex_height = new_tex_height;
					} else {	
						prv_height = new_height;
						prv_tex_height = new_tex_height;
						uv = new_uv;
					}
					i++;
				}			
			/*
				// backtrack UV to the intersection point
				float dt0 = prv_tex_height - prv_height;
				float dt1 = height - tex_height;
				float k = dt0 / (dt0 + dt1);
				uv += uv_step * (1.0 - k);
				*/
				return uv;
			}
		%}

		source %{
		
			mat3 tangent_matrix = _build_mat3(normalize(-v_bitangent), normalize(v_tangent), normalize(v_normal));

			// compute the pixel to view direction in tangent space
			vec4 model_view_pos = _mtx_mul(vInverseModelMatrix, vViewPosition);
			vec3 view_dir = normalize(v_vtx - model_view_pos.xyz);
			
			vec3 tangent_view_dir = normalize(_mtx_mul(transpose(tangent_matrix), view_dir));

			// compute parallax UV offset
			vec2 uv = ParallaxOffsetUV(tangent_view_dir, v_uv, parallax_scale);
		//	vec2 uv = v_uv;
			
			// recompute tangent for the normal computation
			tangent_matrix = _build_mat3(normalize(v_bitangent), normalize(v_tangent), normalize(v_normal));

			// compute normal for reflection
			vec3 n = texture2D(normal_map, uv).xyz;
			n = n * 2.0 - 1.0;
			n = tangent_matrix * n;
			n = normalize(v_normalmatrix * n);
				
			%normal% = n;
			%diffuse% = texture2D(diffuse_map, uv).xyz * texture2D(light_map, uv).xyz;
			%specular% = texture2D(specular_map, uv).xyz;
			%glossiness% = texture2D(glossiness_map, uv).x;
			
		%}
	}
}
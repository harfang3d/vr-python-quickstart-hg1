in {
	tex2D diffuse_map;
	tex2D normal_map;
	tex2D specular_map;
	tex2D glossiness_map;
	tex2D light_map;

	float min_layer = 10;
	float max_layer = 100;

	float parallax_scale = 0.1;
}

variant {

	vertex {
		out {
			vec2 v_uv;
			vec3 v_tangent;
			vec3 v_bitangent;
			vec3 v_normal;
			vec3 v_tangent_view_dir;
		}

		source %{
			v_uv = vUV0;

			v_tangent = vTangent;
			v_bitangent = vBitangent;
			v_normal = vNormal;

			mat3 tangent_matrix = _build_mat3(v_tangent, v_bitangent, v_normal);

			// compute the pixel to view direction in tangent space
			vec4 model_view_pos = _mtx_mul(vInverseModelMatrix, vViewPosition);
			vec3 view_dir = model_view_pos.xyz - vPosition;
			v_tangent_view_dir = _mtx_mul(transpose(tangent_matrix), view_dir);

			%position% = vec4(vPosition, 1.0);
		%}
	}

	pixel {

		source %{
			vec2 uv = v_uv;

			// sample, unpack and transform normal to tangent space
			mat3 tangent_matrix = _build_mat3(normalize(v_tangent), normalize(v_bitangent), normalize(v_normal));

			vec3 n = texture2D(normal_map, uv).xyz;
			n = UnpackVectorFromColor(n);
			n = normalize(tangent_matrix * n);
			n = vNormalViewMatrix * n;

			%normal% = n;
			%diffuse% = texture2D(diffuse_map, uv).xyz * texture2D(light_map, uv).xyz;
			%specular% = texture2D(specular_map, uv).xyz;
			%glossiness% = texture2D(glossiness_map, uv).x;
		%}
	}
}
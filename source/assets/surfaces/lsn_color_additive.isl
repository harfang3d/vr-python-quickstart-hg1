surface {
	blend: additive,
	z-write: false,
	double-sided: false
}
in {
	vec3 diffuse_color;
}

variant {
	vertex {
		out {
			vec2 v_uv;
			vec3 v_normal;
			mat3 v_normalmatrix;
		}

		source %{
			v_uv = vUV0;
			v_normal = vNormal;
			v_normalmatrix = vNormalMatrix;	
		%}
	}

	pixel {
		source %{
			%diffuse% = vec3(0, 0, 0);
			vec3 n = normalize(v_normalmatrix * v_normal);
			%constant% = diffuse_color * (n.xyz * 0.5 + 0.5).zzz; // texture2D(diffuse_map, v_uv).xyz;
		%}
	}
}

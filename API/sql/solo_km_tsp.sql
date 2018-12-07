-- Function: public.pgr_deaparabkm2_5(text, integer[])

-- DROP FUNCTION public.pgr_deaparabkm2_5(text, integer[]);

CREATE OR REPLACE FUNCTION public.pgr_deaparabkm2_5(
    IN tbl text,
    IN pois integer[],
    OUT seq integer,
    OUT gid integer,
    OUT name text,
    OUT heading double precision,
    OUT cost double precision,
    OUT geom geometry)
  RETURNS SETOF record AS
$BODY$

DECLARE
	sql2	text;
        sql     text;
	source  integer;
        target  integer;
        rec     record;
        point   integer;
        pois	int[];
BEGIN
	--inicializar o array
	--pois = string_to_array($2,',');
	seq := 0;
	FOR i IN 2 .. array_upper($2, 1)
	LOOP
	   --RAISE NOTICE 'SOURCE ---- %', pois[i-1];      -- source point!
	   --RAISE NOTICE 'DEST ---- %', pois[i];      -- dest point!

	   -- Shortest path query (TODO: limit extent by BBOX)
	   -- quote_ident => Return the given string suitably quoted to be used as an identifier in an sql statement string. Quotes are added only if necessary (i.e., if the string contains non-identifier characters or would be case-folded). Embedded quotes are properly doubled.

	   sql := 'SELECT id, geom_way, osm_name, '||quote_ident(tbl)||'.cost, source, target,ST_Reverse(geom_way) AS flip_geom FROM ' ||
		  'pgr_dijkstra(''SELECT id as id, source::int, target::int, km::double precision as cost FROM '
				|| quote_ident(tbl) || ''', '|| $2[i-1] || ', ' || $2[i] || ' , false, false), ' || quote_ident(tbl) || ' WHERE id2 = id ORDER BY seq';


	   -- Remember start point
	   point := source;

	   FOR rec IN EXECUTE sql
	   LOOP
		-- Flip geometry (if required)
		IF ( point != rec.source ) THEN
			rec.geom_way := rec.flip_geom;
			point := rec.source;
		ELSE
			point := rec.target;
		END IF;

		-- Calculate heading (simplified)
		EXECUTE 'SELECT degrees( ST_Azimuth(
				ST_StartPoint(''' || rec.geom_way::text || '''),
				ST_EndPoint(''' || rec.geom_way::text || ''') ) )'
			INTO heading;

		-- Return record
		seq     := seq + 1;
		gid     := rec.id;
		name    := rec.osm_name;
		cost    := rec.cost;
		geom    := rec.geom_way;

		sql2 := 'UPDATE '|| quote_ident(tbl) ||' SET km=(km*5) WHERE id='||rec.id;
		EXECUTE sql2;
		RETURN NEXT;
	   END LOOP;
	END LOOP;
        RETURN;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE STRICT
  COST 100
  ROWS 1000;
ALTER FUNCTION public.pgr_deaparabkm2_5(text, integer[])
  OWNER TO amaral;

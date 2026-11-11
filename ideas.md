# Ideas para un futuro

1. Cambiar de VendettaOS/Vendetta-OS/VMC a VendettaOS/VCM como herramienta a parte para separar entre herramienta y el OS que proximamente haré y posibles herramientas futuras fuera del VCM

2. Tener una posible combinación entre DFIR y OSINT para el OS o el VCM, si es así hacer 2 versiones, la DFIR original y la DFIR + OSINT por cosas legales

3. Hacer comandos:
   
- runner: ejecuta cualquier herramienta externa (Volatility, Plaso, Sleuth Kit,...) dentro del caso o de mi herramienta para que haya un mayor control y militarización de herramientas ya existentes y estandarizadas 
- capt: guarda una página web con captura, fecha, hash y registro
- media: verifica imágenes y vídeos (u otro archivo con metadatos), extrae metadatos, calcula hashes y hashes perceptuales (para detectar que dos imágenes son la misma aunque estén recomprimidas o recortadas) y deja anotado qué se verificó y qué no
- geo: bitácora de geolocalización donde anotas el razonamiento (puntos de referencia, sombras, señales, coordenadas, ...) y exporta a KML o GeoJSON (al parecer es el método que usa el periodismo de verificación)
- watch: guarda copias de una página pública cada cierto tiempo y te muestra las diferencias y sirve más que nada para preservar contenido que podría desaparecer o cambiar 
- enti: da un índice de las entidades técnicas que aparecen en el caso (dominios, IPs, handles, correos,...) y en qué evidencia o fuente salió cada una, corelacionarlas con exportación a un grafo
- *scope*: como cada caso debería empezar con una nota de alcance (quién autorizó la investigación, con qué base, qué está dentro y qué fuera, cuánto tiempo se conservan los datos, ...) y las demás herramientas la consultan y avisa si capturas algo fuera de ese alcance [ver si tengo la suficiente habilidad para hacer esto...]

####Puede ser que algunas cosas se hagan, otras se modifiquen o directamente se deseche... 

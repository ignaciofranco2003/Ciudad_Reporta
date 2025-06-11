use ciudad_reporta;

INSERT INTO usuarios (email, rol) VALUES
('juan@example.com', 'usuario'),
('lucia@example.com', 'usuario'),
('carlos@example.com', 'usuario'),
('admin@example.com', 'administrador');

INSERT INTO reporte (fk_id_categoria, descripcion, latitud, longitud, imagen_URL, solucionada, fk_id_usuario, estado)
VALUES
(2,'Bache en calle San Martín', -33.677, -59.663, 'uploads/bache1.jpg', FALSE, 1, 'Activo'),
(1,'Luminaria rota en la plaza', -33.680, -59.660, 'uploads/luminaria1.jpg', FALSE, 2, 'Activo');

INSERT INTO reporte (fk_id_categoria, descripcion, latitud, longitud, imagen_URL, solucionada, fk_id_usuario, estado)
VALUES
(5,'Tapa de alcantarilla faltante', -33.675, -59.668, 'uploads/alcantarilla1.jpg', FALSE, 1, 'Pendiente'),
(3,'Semáforo fuera de servicio', -33.678, -59.662, 'uploads/semaforo1.jpg', FALSE, 3, 'Pendiente');

INSERT INTO reporte (fk_id_categoria, descripcion, latitud, longitud, imagen_URL, solucionada, fk_id_usuario, estado)
VALUES
(4,'Contenedor de basura roto', -33.679, -59.661, 'uploads/contenedor1.jpg', TRUE, 2, 'Solucionado'),
(5,'Desborde cloacal resuelto', -33.676, -59.664, 'uploads/cloaca1.jpg', TRUE, 3, 'Solucionado');


INSERT INTO admins (id_usuario, password) VALUES (4, 'admin1234');

#CREATE DATABASE IF NOT EXISTS ciudad_reporta

#USE ciudad_reporta

/*
INSERT INTO categorias_problematicas (nombre_categoria) VALUES
("Alumbrado publico"),
("Calles y veredas"),
("Semaforos"),
("Basura y limpieza"),
("Cloacas y desagues"),
("Otros");
*/

/*
CREATE TABLE IF NOT EXISTS usuarios (
	id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
	email VARCHAR(120) UNIQUE NOT NULL,
	rol VARCHAR(20) NOT NULL
);
*/

/*
CREATE TABLE IF NOT EXISTS reporte (
	id_reporte INT AUTO_INCREMENT PRIMARY KEY,
    fk_id_categoria INT,
	descripcion VARCHAR (255) NOT NULL,
    latitud FLOAT NOT NULL,
    longitud FLOAT NOT NULL,
    imagen_URL VARCHAR (50) NOT NULL,
	solucionada BOOLEAN DEFAULT FALSE,
	fk_id_usuario INT,
	estado VARCHAR(20) DEFAULT 'activo',
	FOREIGN KEY (fk_id_usuario) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (fk_id_categoria) REFERENCES categorias_problematicas(id_categoria_problematica)
);
*/

/*
CREATE TABLE IF NOT EXISTS categorias_problematicas (
	id_categoria_problematica INT AUTO_INCREMENT PRIMARY KEY,
	nombre_categoria VARCHAR(100) NOT NULL
);
*/

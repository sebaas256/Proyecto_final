import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau

# Directorios de datos
new_train_dir = r'C:\Users\cseba\OneDrive\Escritorio\Proyecto_final\modelo_lstm_lsp-main\gestos\train'  # Ruta a los nuevos datos de entrenamiento
new_val_dir = r'C:\Users\cseba\OneDrive\Escritorio\Proyecto_final\modelo_lstm_lsp-main\gestos\val'      # Ruta a los nuevos datos de validación

# Parámetros de entrenamiento
img_size = (224, 224)
batch_size = 32
num_epochs = 20  # Aumentado para permitir un entrenamiento más exhaustivo
initial_learning_rate = 0.0001

# Cargar el modelo preentrenado
existing_model_path = r'C:\Users\cseba\OneDrive\Escritorio\Proyecto_final\best_model.keras'
base_model = tf.keras.models.load_model(existing_model_path)

# Preparación de los nuevos datos
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=40,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'
)

val_datagen = ImageDataGenerator(rescale=1./255)

new_train_generator = train_datagen.flow_from_directory(
    new_train_dir, 
    target_size=img_size, 
    batch_size=batch_size, 
    class_mode='categorical'
)

new_val_generator = val_datagen.flow_from_directory(
    new_val_dir, 
    target_size=img_size, 
    batch_size=batch_size, 
    class_mode='categorical'
)

# Descongelar las últimas capas del modelo base para el fine-tuning
fine_tune_at = 100  # Número de capas a descongelar
for layer in base_model.layers[:fine_tune_at]:
    layer.trainable = False
for layer in base_model.layers[fine_tune_at:]:
    layer.trainable = True

# Añadir nuevas capas al modelo si es necesario (opcional)
x = base_model.layers[-2].output  # Asumiendo que el penúltimo layer es GlobalAveragePooling2D
x = Dense(1024, activation='relu', name='dense_1024_20')(x)
x = Dropout(0.5, name='dropout_4')(x)  # Aumentar Dropout para mayor regularización
x = Dense(512, activation='relu', name='dense_512_121')(x)
x = Dropout(0.5, name='dropout_255_1')(x)
predictions = Dense(new_train_generator.num_classes, activation='softmax', name='predictions')(x)

# Crear el nuevo modelo
model = Model(inputs=base_model.input, outputs=predictions)

# Compilar el modelo
model.compile(optimizer=Adam(learning_rate=initial_learning_rate), loss='categorical_crossentropy', metrics=['accuracy'])

# Callbacks
early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5, min_lr=1e-6)
model_checkpoint = ModelCheckpoint('best_model2.keras', save_best_only=True, monitor='val_accuracy', mode='max')

# Entrenamiento del modelo
model.fit(
    new_train_generator, 
    epochs=num_epochs, 
    validation_data=new_val_generator, 
    callbacks=[early_stopping, reduce_lr, model_checkpoint]
)

# Guardar el nuevo modelo
model.save('Modelo_varias_personas.keras')
Chocolate Beans in Glass
========================

In this subsequent tutorial, once again, we will focus on our tasty chocolate beans. We will introduce a further object -- a glass with transmissive, refractive material -- to the scene, which influences the view on the particles. The perspective of our camera will be subject to variation. Our main focus lies on the difference between the particles' behavior and appearance on the final images when comparing the scene with and without glass.

At a Glance
-----------

.. image:: ../_static/tuts/chocBeans_glassTable/AAG_0.png
    :width: 32.5 %
.. image:: ../_static/tuts/chocBeans_glassTable/AAG_1.png
    :width: 32.5 %
.. image:: ../_static/tuts/chocBeans_glassTable/AAG_2.png
    :width: 32.5 %
.. image:: ../_static/tuts/chocBeans_glassTable/AAG_3.png
    :width: 32.5 %
.. image:: ../_static/tuts/chocBeans_glassTable/AAG_4.png
    :width: 32.5 %
.. image:: ../_static/tuts/chocBeans_glassTable/AAG_5.png
    :width: 32.5 %

What We Will Learn
------------------

* Closer look at ``RelaxCollisions`` function, incl. ``dry_run``
* Enable/disable scene objects
* Slim down recipe with inheritance
* Use multirun to output image series
* Randomize scene by various parameters

Step 1: Tidy Up!
----------------

We start this tutorial by using the ``inheritance`` mechanism a little bit different than before: Our recipe from the previous tutorial grew to a proud size of 303 code lines, all together.

.. code-block:: yaml
    :caption: chocBeans_table.yaml
    :emphasize-lines: 9,37

    # Initializing and seeding
    defaults: …
    initial_runtime_state: …
    # Defining blueprints
    blueprints:
      measurement_techniques: …
      particles: …
    # Physical boundary conditions
    process_conditions:
      feature_criteria:
        IsCat1: …
        ⋮
        IsCat8: …
        IsPink: …
      sets: 
        Category1: …
        ⋮
        Category8: …
        PinkParticles: …
      feature_variabilities:
        CameraNearTable: …
        InitialParticleLocation: …
        ParticleDimension: …
        ParticleWidth: …
        ParticleHeight: …
        PinkColor: …
        RedColor: …
        OrangeColor: …
        YellowColor: …
        GreenColor: …
        BlueColor: …
        PurpleColor: …
        BrownColor: …
        RenderingResolutionPercentage: …
        CyclesSamples: …
    # Procedural steps of synthetization chain
    synth_chain:
      feature_generation_steps:
        - _target_: $builtins.InvokeBlueprints # MeasurementTechnique …
        - _target_: $builtins.InvokeBlueprints # Particles …
        - _target_: $builtins.TriggerFeatureUpdate # cam_location_z …
        - _target_: $builtins.TriggerFeatureUpdate # location …
        - _target_: $builtins.TriggerFeatureUpdate # dimensions …
        - _target_: $builtins.TriggerFeatureUpdate # width …
        - _target_: $builtins.TriggerFeatureUpdate # height …
        - _target_: $builtins.TriggerFeatureUpdate # color(pink) …
        - _target_: $builtins.TriggerFeatureUpdate # color(red) …
        - _target_: $builtins.TriggerFeatureUpdate # color(orange) …
        - _target_: $builtins.TriggerFeatureUpdate # color(yellow) …
        - _target_: $builtins.TriggerFeatureUpdate # color(green) …
        - _target_: $builtins.TriggerFeatureUpdate # color(blue) …
        - _target_: $builtins.TriggerFeatureUpdate # color(purple) …
        - _target_: $builtins.TriggerFeatureUpdate # color(brown) …
        - _target_: $builtins.RelaxCollisions # avoid intersections …
        - _target_: $builtins.RelaxCollisions # gravity …
        - _target_: $builtins.TriggerFeatureUpdate # resolution …
        - _target_: $builtins.TriggerFeatureUpdate # render samples …
      rendering_steps:
        - _target_: $builtins.SaveState …
        - _target_: $builtins.RenderParticlesTogether # real …
        - _target_: $builtins.RenderParticlesTogether # cat(all) …
        - _target_: $builtins.RenderParticlesTogether # cat(pink) …
        - _target_: $builtins.RenderParticlesIndividually # pink …

Now -- to make navigating and handling the recipe easier and less prone to errors -- we want to sort the parts a little bit and shrink down the main recipe to those elements, which are essential and those elements, which we often want to touch.

First, we will create three new files:

* ``chocBeans_glassTable.yaml``, our main recipe
* ``s_SceneVariation.yaml``, scene description, incl. blueprints
* ``s_BeanParams.yaml``, the parameters of our ``Beads``
* ``s_ColorCategories.yaml``, sets and color definitions

As a first step, in our main recipe, we add our usual ``Initializing and seeding`` block. Under ``defaults:``, we will now include those three further files (we used the prefix ``s_`` here to mark the files as "supplementary" = not a stand-alone recipe; this naming convention is arbitrary).

.. code-block:: yaml
    :caption: chocBeans_glassTable.yaml

    # Initializing and seeding
    defaults:
      - BaseRecipe
      - s_SceneVariation
      - s_BeanParams
      - s_ColorCategories
      - _self_
    initial_runtime_state:
      seed: 42

As mentioned above, we want to keep the parts in the main recipe, which we touch more often and outsource the parts, we rarely or never touch after definition. So, we continue in our main recipe and copy over the two ``feature_variabilities`` for the features ``resolution_percentage`` and ``cycles_samples``.

.. code-block:: yaml
    :caption: chocBeans_glassTable.yaml
    :emphasize-lines: 4-16

    # Initializing and seeding
    defaults: …
    initial_runtime_state: …
    # Physical boundary conditions
    process_conditions:
      feature_variabilities:
        RenderingResolutionPercentage:
          feature_name: resolution_percentage
          variability:
            _target_: $builtins.Constant
            value: 25
        CyclesSamples:
          feature_name: cycles_samples
          variability:
            _target_: $builtins.Constant
            value: 64

We will not need `any` other ``process_conditions`` in our main recipe. However unfortunately, the ``synth_chain`` we need to copy over as a whole, since we want to make some changes here. As mentioned earlier, in the current version of ``synthPIC2``, it is `not` allowed to change/add only single elements of the both lists ``feature_generation_steps`` and ``rendering_steps`` by inheritance, but only to replace them as a whole. In the latter case -- in the sequence defined at the very top under ``defaults:`` -- every newly introduced list of ``feature_generation_steps`` or ``rendering_steps`` from a subsequent recipe will completely replace its predecessor.

.. code-block:: yaml
    :caption: chocBeans_glassTable.yaml

    # Procedural steps of synthetization chain
    synth_chain:
      feature_generation_steps:
        - _target_: $builtins.InvokeBlueprints
          affected_set_name: AllMeasurementTechniqueBlueprints
        - _target_: $builtins.InvokeBlueprints
          affected_set_name: AllParticleBlueprints
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: CameraNearTable
          affected_set_name: AllMeasurementTechniques
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: InitialParticleLocation
          affected_set_name: AllParticles
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: ParticleDimension
          affected_set_name: AllParticles
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: ParticleWidth
          affected_set_name: AllParticles
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: ParticleHeight
          affected_set_name: AllParticles 
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: PinkColor
          affected_set_name: Category1
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: RedColor
          affected_set_name: Category2
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: OrangeColor
          affected_set_name: Category3
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: YellowColor
          affected_set_name: Category4
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: GreenColor
          affected_set_name: Category5
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: BlueColor
          affected_set_name: Category6
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: PurpleColor
          affected_set_name: Category7
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: BrownColor
          affected_set_name: Category8
        - _target_: $builtins.RelaxCollisions
          affected_set_name: AllParticles
          num_frames: 5
          time_scale: 10
          collision_shape: CONVEX_HULL
        - _target_: $builtins.RelaxCollisions
          affected_set_name: AllParticles
          use_gravity: True
          damping: 0.07
          friction: 0.999
          restitution: 0.001
          collision_margin: 0.001
          num_frames: 200
          collision_shape: CONVEX_HULL
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: RenderingResolutionPercentage
          affected_set_name: AllMeasurementTechniques
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: CyclesSamples
          affected_set_name: AllMeasurementTechniques
      rendering_steps:
        - _target_: $builtins.SaveState
          name: state
        - _target_: $builtins.RenderParticlesTogether
          rendering_mode: real
          do_save_features: True
        - _target_: $builtins.RenderParticlesTogether
          rendering_mode: categorical
          output_file_name_prefix: all_
        - _target_: $builtins.RenderParticlesTogether
          rendering_mode: categorical
          set_name_of_interest: PinkParticles
          output_file_name_prefix: pink_
        - _target_: $builtins.RenderParticlesIndividually
          rendering_mode: categorical
          set_name_of_interest: PinkParticles
          subfolder: pink

With the main recipe file ``chocBeans_glassTable.yaml`` we're done. Let's now outsource the rest of our previous recipe file ``chocBeans_table.yaml``. In the newly created, supplementary file ``s_SceneVariation.yaml``, we add all information about the ``blueprints``, the general scene layout as well as the perspective view.

.. code-block:: yaml
    :caption: s_SceneVariation.yaml

    # Defining blueprints
    blueprints:
      measurement_techniques:
        TopCamInAir:
          measurement_technique_prototype_name: woodTable_sideCam
          measurement_volume_material_prototype_name: vacuum
          background_material_prototype_name: wood
      particles:
        Bead:
          geometry_prototype_name: ellipsoid
          material_prototype_name: colored_subtle
          parent: MeasurementVolume
          number: 200
    # Physical boundary conditions
    process_conditions:
      feature_variabilities:
        CameraNearTable:
          feature_name: cam_location_z
          variability:
            _target_: $builtins.Constant
            value: -35.0

The second newly created supplementary file ``s_BeanParams.yaml`` will hold all information, i.e. ``features`` we want to manipulate, about our particles.

.. code-block:: yaml
    :caption: s_BeanParams.yaml

    # Physical boundary conditions
    process_conditions:
      feature_variabilities:
        InitialParticleLocation:
          feature_name: location
          variability:
            _target_: $builtins.UniformlyRandomLocationInMeasurementVolume
        ParticleDimension:
          feature_name: dimensions
          variability:
            _target_: $builtins.UniformDistribution3dHomogeneous
            location: 3.58
            scale: 0.6
        ParticleWidth:
          feature_name: width
          variability:
            _target_: $builtins.UniformDistributionNdHomogeneous
            location: 0.85
            scale: 0.15
            num_dimensions: 1
        ParticleHeight:
          feature_name: height
          variability:
            _target_: $builtins.UniformDistributionNdHomogeneous
            location: 0.475
            scale: 0.15
            num_dimensions: 1

The last of the three supplementary files ``s_ColorCategories.yaml`` defines all the ``feature_criteria``, the ``sets`` and the ``feature_variabilities``, which are related to color definition.

.. code-block:: yaml
    :caption: s_ColorCategories.yaml

    # Physical boundary conditions
    process_conditions:
      feature_criteria:
        IsCat1:
          _target_: $plugins.official.InCompartment
          feature_name: location_z
          compartment_no: 1
          compartments_total: 8
          default_return_value: False
        IsCat2:
          _target_: $plugins.official.InCompartment
          feature_name: location_z
          compartment_no: 2
          compartments_total: 8
          default_return_value: False
        IsCat3:
          _target_: $plugins.official.InCompartment
          feature_name: location_z
          compartment_no: 3
          compartments_total: 8
          default_return_value: False
        IsCat4:
          _target_: $plugins.official.InCompartment
          feature_name: location_z
          compartment_no: 4
          compartments_total: 8
          default_return_value: False
        IsCat5:
          _target_: $plugins.official.InCompartment
          feature_name: location_z
          compartment_no: 5
          compartments_total: 8
          default_return_value: False
        IsCat6:
          _target_: $plugins.official.InCompartment
          feature_name: location_z
          compartment_no: 6
          compartments_total: 8
          default_return_value: False
        IsCat7:
          _target_: $plugins.official.InCompartment
          feature_name: location_z
          compartment_no: 7
          compartments_total: 8
          default_return_value: False
        IsCat8:
          _target_: $plugins.official.InCompartment
          feature_name: location_z
          compartment_no: 8
          compartments_total: 8
          default_return_value: False
        IsPink:
          _target_: $plugins.official.InHsvRange
          feature_name: color
          h_min: 0.945
          h_max: 0.950
          s_min: 0.895
          s_max: 0.900
          v_min: 0.648
          v_max: 0.653
          default_return_value: False
      sets: 
        Category1:
          criterion: $IsParticle and $IsCat1
        Category2:
          criterion: $IsParticle and $IsCat2
        Category3:
          criterion: $IsParticle and $IsCat3
        Category4:
          criterion: $IsParticle and $IsCat4
        Category5:
          criterion: $IsParticle and $IsCat5
        Category6:
          criterion: $IsParticle and $IsCat6
        Category7:
          criterion: $IsParticle and $IsCat7
        Category8:
          criterion: $IsParticle and $IsCat8
        PinkParticles:
          criterion: $IsParticle and $IsPink
      feature_variabilities:
        PinkColor:
          feature_name: color
          variability:
            _target_: $plugins.official.RandomHsvColorAsRgb
            h_min: 0.945
            h_max: 0.950
            s_min: 0.895
            s_max: 0.900
            v_min: 0.648
            v_max: 0.653
        RedColor:
          feature_name: color
          variability:
            _target_: $plugins.official.RandomHsvColorAsRgb
            h_min: 0.990
            h_max: 0.995
            s_min: 0.995
            s_max: 1.000
            v_min: 0.448
            v_max: 0.453
        OrangeColor:
          feature_name: color
          variability:
            _target_: $plugins.official.RandomHsvColorAsRgb
            h_min: 0.020
            h_max: 0.025
            s_min: 0.995
            s_max: 1.000
            v_min: 0.895
            v_max: 0.900
        YellowColor:
          feature_name: color
          variability:
            _target_: $plugins.official.RandomHsvColorAsRgb
            h_min: 0.087
            h_max: 0.092
            s_min: 0.945
            s_max: 0.950
            v_min: 0.862
            v_max: 0.867
        GreenColor:
          feature_name: color
          variability:
            _target_: $plugins.official.RandomHsvColorAsRgb
            h_min: 0.321
            h_max: 0.326
            s_min: 0.770
            s_max: 0.775
            v_min: 0.253
            v_max: 0.258
        BlueColor:
          feature_name: color
          variability:
            _target_: $plugins.official.RandomHsvColorAsRgb
            h_min: 0.622
            h_max: 0.627
            s_min: 0.846
            s_max: 0.851
            v_min: 0.547
            v_max: 0.552
        PurpleColor:
          feature_name: color
          variability:
            _target_: $plugins.official.RandomHsvColorAsRgb
            h_min: 0.716
            h_max: 0.721
            s_min: 0.801
            s_max: 0.806
            v_min: 0.348
            v_max: 0.353
        BrownColor:
          feature_name: color
          variability:
            _target_: $plugins.official.RandomHsvColorAsRgb
            h_min: 0.020
            h_max: 0.025
            s_min: 0.796
            s_max: 0.801
            v_min: 0.082
            v_max: 0.087

When we render our newly created main recipe, which contains basically "only" a better sorted version of our recent recipe ``chocBeans_table``, we will find -- surprise, surprise -- `exactly` the same output in the folder ``output/chocBeans_glassTable/<YYYY-MM-DD_hh-mm-ss>/run0/`` and its subfolders, as we produced in the end of the previous tutorial.

.. code-block:: python

    python run.py --config-dir=recipes --config-name=chocBeans_glassTable

.. image:: ../_static/tuts/chocBeans_glassTable/startPrevRecipe_real.png
    :width: 32.5 %
.. image:: ../_static/tuts/chocBeans_glassTable/startPrevRecipe_categ_all.png
    :width: 32.5 %
.. image:: ../_static/tuts/chocBeans_glassTable/startPrevRecipe_categ_pink.png
    :width: 32.5 %
.. image:: ../_static/tuts/chocBeans_glassTable/startPrevRecipe_categ_singlePink_1.png
    :width: 32.5 %
.. image:: ../_static/tuts/chocBeans_glassTable/startPrevRecipe_categ_singlePink_2.png
    :width: 32.5 %
.. image:: ../_static/tuts/chocBeans_glassTable/startPrevRecipe_categ_singlePink_3.png
    :width: 32.5 %

Okay, easy start. Wasn't it? Just some copy-pasting. In the next step, we will have a look at our main goal in this tutorial. But before we go there, here's a little overview of the recipe files, which we just created. Take this little summary of the long code blocks' content from before to recap this first step and to appreciate the possibility to use inheritance for recipes.

.. code-block:: yaml
    :caption: chocBeans_glassTable.yaml
    :emphasize-lines: 4-6

    # Initializing and seeding
    defaults:
      - BaseRecipe
      - s_SceneVariation
      - s_BeanParams
      - s_ColorCategories
      - _self_
    initial_runtime_state: …
    # Physical boundary conditions
    process_conditions:
      feature_variabilities:
        RenderingResolutionPercentage: …
        CyclesSamples: …
    # Procedural steps of synthetization chain
    synth_chain:
      feature_generation_steps: …
      rendering_steps: …

.. code-block:: yaml
    :caption: s_SceneVariation.yaml

    # Defining blueprints
    blueprints:
      measurement_techniques: …
      particles: …
    # Physical boundary conditions
    process_conditions:
      feature_variabilities:
        CameraNearTable: …

.. code-block:: yaml
    :caption: s_BeanParams.yaml

    # Physical boundary conditions
    process_conditions:
      feature_variabilities:
        InitialParticleLocation: …
        ParticleDimension: …
        ParticleWidth: …
        ParticleHeight: …

.. code-block:: yaml
    :caption: s_ColorCategories.yaml

    # Physical boundary conditions
    process_conditions:
      feature_criteria:
        IsCat1: …
        ⋮
        IsCat8: …
        IsPink: …
      sets: 
        Category1: …
        ⋮
        Category8: …
        PinkParticles: …
      feature_variabilities:
        PinkColor: …
        ⋮
        BrownColor: …

Step 2: What to Achieve and How to Approach
-------------------------------------------

As promised, let's try to envision where we're going here: We first just took the recipe from the previous tutorial. We sorted it into several helper/supplementary files for the sake of being able to keep the overview and to still be able to handle it.

Next, we want to introduce a further object, namely a `glass`. We place this below our chocolate beans to catch those falling particles during the physics simulation.

Then we will have two cases for our synthesized particles: The first `without`, the second `with` the glass, which was introduced to the scene.

.. raw:: html

    <video controls loop width="100%" poster="../_static/tuts/chocBeans_glassTable/compareGlass_STD_poster.png" src="../_static/tuts/chocBeans_glassTable/compareGlass_STD.mp4"></video> 

We will compare these two and focus on some questions.

* "How will the particles' movement differ between the cases with and without glass, starting with exactly the same location of each particle?"
* "How do the particles behave, assuming different physics?", i.e. different parameters of the ``RelaxCollisions`` function.
* "How will the particles' appearance differ with and without glass?"
* "What's the influence of the gravity?", i.e. changing the gravity vector
* "How many chocolate beans are good for us?"

We do this rather detailed investigation of how exactly the particles fall, since this is our last fine-tuning step, before we go into "series production", i.e. batch processing to output multiple randomized images -- all of course from chocolate beans and with every ``feature`` restricted only to the allowed ranges, which were specified by us.

To actually do something in this step, let's `at least` prepare the scene for the experiments with parameter variation, which we will perform in the next step. We will first "activate" the glass. To our supplementary file ``s_SceneVariation.yaml``, we will add two more ``feature_variabilities``.

.. code-block:: yaml
    :caption: s_SceneVariation.yaml
    :emphasize-lines: 9-18

    # Defining blueprints
    blueprints:
      measurement_techniques: …
      particles: …
    # Physical boundary conditions
    process_conditions:
      feature_variabilities:
        CameraNearTable: …
        ShowGlass:
          feature_name: glass_hide
          variability:
            _target_: $builtins.Constant
            value: False
        CollisionGlass:
          feature_name: glass_collision
          variability:
            _target_: $builtins.Constant
            value: True

In our main recipe ``chocBeans_glassTable.yaml``, we add the corresponding ``feature_generation_steps``, because our main recipe holds the complete list of ``feature_generation_steps``. Let's add the two ``TriggerFeatureUpdates`` directly after our two ``InvokeBlueprints`` steps.

.. code-block:: yaml
    :caption: chocBeans_glassTable.yaml
    :emphasize-lines: 5-10

    synth_chain:
      feature_generation_steps:
        - _target_: $builtins.InvokeBlueprints …
        - _target_: $builtins.InvokeBlueprints …
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: ShowGlass
          affected_set_name: AllMeasurementTechniques
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: CollisionGlass
          affected_set_name: AllMeasurementTechniques
        - _target_: $builtins.TriggerFeatureUpdate …

Executing the recipe will output the rendered image showing our chocolate beans captured by the glass.

.. image:: ../_static/tuts/chocBeans_glassTable/chocBeansGlass_offset.png
    :alt: Glass with chocolate beans with offset view

Okay, the glass is there, but the view isn't nice. To change this, let's just remove (or comment out) the corresponding ``TriggerFeatureUpdate`` step from our list of ``feature_generation_steps``.

.. code-block:: yaml
    :caption: chocBeans_glassTable.yaml
    :emphasize-lines: 9-11

    synth_chain:
      feature_generation_steps:
        - _target_: $builtins.InvokeBlueprints …
        - _target_: $builtins.InvokeBlueprints …
        - _target_: $builtins.TriggerFeatureUpdate …
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: CollisionGlass
          affected_set_name: AllMeasurementTechniques
        # - _target_: $builtins.TriggerFeatureUpdate
        #   feature_variability_name: CameraNearTable
        #   affected_set_name: AllMeasurementTechniques
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: InitialParticleLocation
          affected_set_name: AllParticles

If you like, you could also remove the ``feature variability`` from our ``process_conditions`` in the file ``s_SceneVariation.yaml``. However, you could also just leave it there. Doesn't matter, it's personal preference depending on how keen you are with tidying up (or if you purposefully want to leave those code snippets for later playing around & fast access to change those features once again).

We will change two more things. First, let's turn on the ``dry_run`` for our `second` ``RelaxCollisions`` function again: We want to see how the particles are falling in the next step!

.. code-block:: yaml
    :caption: chocBeans_glassTable.yaml
    :emphasize-lines: 11

        - _target_: $builtins.RelaxCollisions …
        - _target_: $builtins.RelaxCollisions
          affected_set_name: AllParticles
          use_gravity: True
          damping: 0.07
          friction: 0.999
          restitution: 0.001
          collision_margin: 0.001
          num_frames: 200
          collision_shape: CONVEX_HULL
          dry_run: True

Second, we comment out the categorical rendering steps for the moment. We are not interested in those at the moment. But don't worry, we'll turn it on again, later in step 4.

.. code-block:: yaml
    :caption: chocBeans_glassTable.yaml
    :emphasize-lines: 6-16

      rendering_steps:
        - _target_: $builtins.SaveState …
        - _target_: $builtins.RenderParticlesTogether
          rendering_mode: real
          do_save_features: True
        # - _target_: $builtins.RenderParticlesTogether
        #   rendering_mode: categorical
        #   output_file_name_prefix: all_
        # - _target_: $builtins.RenderParticlesTogether
        #   rendering_mode: categorical
        #   set_name_of_interest: PinkParticles
        #   output_file_name_prefix: pink_
        # - _target_: $builtins.RenderParticlesIndividually
        #   rendering_mode: categorical
        #   set_name_of_interest: PinkParticles
        #   subfolder: pink 

If we `would` turn off the particles for a second (just for this one render: comment out the ``InvokeBlueprints`` of our particles and the ``TriggerFeatureUpdates`` for color), we'd see our glass on the table -- with well positioned camera view. Everything is prepared now for the next step with experiments to investigate parameter variation.

.. image:: ../_static/tuts/chocBeans_glassTable/glassOnly.png
    :alt: Only empty glass in the middle of the camera view

Step 3: Playing God and Change the Physics
------------------------------------------

If you commented them out to see only the glass in the last step, comment them in again, the lines for ``InvokeBlueprints`` of our particles and the ``TriggerFeatureUpdates`` for color.

Now, you are free to change and play around with some parameters. You could try the following variations (see also subsequent images):

* Simulate with and without glass (try different combinations of ``ShowGlass`` and/or ``CollisionGlass``).
* Use our previous parameters of ``RelaxCollisions``, try changing parameters of ``RelaxCollisions``, e.g. play around with ``damping``, ``friction`` and ``restitution``. Try new parameters ``mass``, ``gravity``. (Hints: leave ``dry_run`` turned on and keep ``SaveState`` in ``rendering_steps`` to observe the effect. A smaller value for ``num_frames`` is advised. When doing large parameter variation experiments, multirun should be used, see next step.)
* Let the particles fall sideways... everything possible! Therefore, you would need to change the ``gravity`` vector -- keep in mind: this should be input as a list.
* You could try more particles & longer (``num_frames``) simulation time.

.. image:: ../_static/tuts/chocBeans_glassTable/wGlass_wCollision.png
    :width: 24.5 %
.. image:: ../_static/tuts/chocBeans_glassTable/AAG_0.png
    :width: 24.5 %
.. image:: ../_static/tuts/chocBeans_glassTable/collisionOnly.png
    :width: 24.5 %
.. image:: ../_static/tuts/chocBeans_glassTable/gravitySideways.png
    :width: 24.5 %

The example images show the behavior of our chocolate beans, when a glass is present and when there is no glass and the particles can freely distribute on the table. Furthermore, the third image shows how the particle appearance would look like if there would be a physical (``CollisionGlass``), but not a visual (``ShowGlass``) influence of the glass. This case is quite interesting: It demonstrates, how our particles would look like -- placed in the same position, but if glass would be invisible. Meaning, if there wouldn't be the refraction of the glass, which distorts the particles' appearances and eventually moves/changes the information of each particle (i.e. colored pixels) to different pixel locations in the final image. If your use case would be, e.g. to measure the 2D projected area of those chocolate beans with a certain color in the final image, the influence of how strong the glass distorts this truth could be quantified. The last image shows the result if our particles would fall sideways, with a different ``gravity`` vector applied, see code snippet below.

.. code-block:: yaml
    :caption: chocBeans_glassTable.yaml
    :emphasize-lines: 9-12

        - _target_: $builtins.RelaxCollisions …
        - _target_: $builtins.RelaxCollisions
          affected_set_name: AllParticles
          use_gravity: True
          damping: 0.07
          friction: 0.999
          restitution: 0.001
          collision_margin: 0.001
          gravity:
            - +5
            - -5
            - 0
          num_frames: 200
          collision_shape: CONVEX_HULL
          dry_run: True

After some variation of our chocolate beans' quantity, a number of 500 particles looks quite appropriate, resulting in a completely filled glass and a few particles falling on the wooden table -- not too many, just the right amount. Also after tinkering around with the parameters of ``RelaxCollisions``, we seem to have found our final parametrization, see video below (extended to ``num_frames: 600`` as opposed to ``num_frames: 200`` for our final renders) and subsequent code snippets.

.. raw:: html

    <video controls loop width="100%" poster="../_static/tuts/chocBeans_glassTable/500fA_wm_poster.png" src="../_static/tuts/chocBeans_glassTable/500_fullAni_wm.mp4"></video> 

.. code-block:: yaml
    :caption: s_SceneVariation.yaml
    :emphasize-lines: 9

    # Defining blueprints
    blueprints:
      measurement_techniques: …
      particles:
        Bead:
          geometry_prototype_name: ellipsoid
          material_prototype_name: colored_subtle
          parent: MeasurementVolume
          number: 500

.. code-block:: yaml
    :caption: chocBeans_glassTable.yaml
    :emphasize-lines: 3,6,12-14

    - _target_: $builtins.RelaxCollisions
      affected_set_name: AllParticles
      mass: 0.0012
      num_frames: 5
      time_scale: 10
      collision_margin: 0.001
      collision_shape: CONVEX_HULL
    - _target_: $builtins.RelaxCollisions
      affected_set_name: AllParticles
      use_gravity: True
      damping: 0.07
      friction: 0.4
      restitution: 0.1
      mass: 0.0012
      collision_margin: 0.001
      num_frames: 200
      collision_shape: CONVEX_HULL
      dry_run: True

Step 4: Variation in Series Production
--------------------------------------

In this last step of our tutorial, we want to go for the fully automated particle generation under (pseudo-)random parameter variation of the scene. We do so, by just simply varying the ``initial_runtime_state.seed``.

But first let's comment in the categorical ``render_steps`` again.

.. code-block:: yaml
    :caption: chocBeans_glassTable.yaml
    :emphasize-lines: 6-16

      rendering_steps:
        - _target_: $builtins.SaveState …
        - _target_: $builtins.RenderParticlesTogether
          rendering_mode: real
          do_save_features: True
        - _target_: $builtins.RenderParticlesTogether
          rendering_mode: categorical
          output_file_name_prefix: all_
        - _target_: $builtins.RenderParticlesTogether
          rendering_mode: categorical
          set_name_of_interest: PinkParticles
          output_file_name_prefix: pink_
        - _target_: $builtins.RenderParticlesIndividually
          rendering_mode: categorical
          set_name_of_interest: PinkParticles
          subfolder: pink 

Furthermore, we will add several new ``feature_variabilities`` to our ``s_SceneVariation.yaml`` file.

.. code-block:: yaml
    :caption: s_SceneVariation.yaml
    :emphasize-lines: 11-52

    # Defining blueprints
    blueprints:
      measurement_techniques: …
      particles: …
    # Physical boundary conditions
    process_conditions:
      feature_variabilities:
        CameraNearTable: …
        ShowGlass: …
        CollisionGlass: …
        CameraRotation:
          feature_name: cam_rotation
          variability:
            _target_: $builtins.UniformDistributionNdHomogeneous
            location: -0.0523598775598299
            scale: 0.10471975511966               
            num_dimensions: 1
        CameraAltitude:
          feature_name: cam_altitude
          variability:
            _target_: $builtins.UniformDistributionNdHomogeneous
            location: -0.15707963267949
            scale: 0.314159265358979
            num_dimensions: 1
        CameraAzimuth:
          feature_name: cam_azimuth
          variability:
            _target_: $builtins.UniformDistributionNdHomogeneous
            location: 0.0
            scale: 6.28318530717959
            num_dimensions: 1
        GlassRotation:
          feature_name: glass_rotation
          variability:
            _target_: $builtins.UniformDistributionNdHomogeneous
            location: 0.0
            scale: 0.698131700797732
            num_dimensions: 1
        TableRotation:
          feature_name: table_rotation
          variability:
            _target_: $builtins.UniformDistributionNdHomogeneous
            location: 0.0
            scale: 6.28318530717959
            num_dimensions: 1
        WoodTexture:
          feature_name: texture_seed
          variability:
            _target_: $builtins.UniformDistributionNdHomogeneous
            location: 0
            scale: 1000
            num_dimensions: 1

...and we need to trigger those in our main recipe file ``chocBeans_glassTable.yaml``

.. code-block:: yaml
    :caption: chocBeans_glassTable.yaml
    :emphasize-lines: 8-25

    synth_chain:
      feature_generation_steps:
        - _target_: $builtins.InvokeBlueprints …
        ⋮
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: BrownColor
          affected_set_name: Category8
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: CameraRotation
          affected_set_name: AllMeasurementTechniques
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: CameraAltitude
          affected_set_name: AllMeasurementTechniques
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: CameraAzimuth
          affected_set_name: AllMeasurementTechniques
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: GlassRotation
          affected_set_name: AllMeasurementTechniques
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: TableRotation
          affected_set_name: AllMeasurementTechniques
        - _target_: $builtins.TriggerFeatureUpdate
          feature_variability_name: WoodTexture
          affected_set_name: AllMeasurementTechniques
        - _target_: $builtins.RelaxCollisions …
        ⋮

These new feature variations will introduce random variations of the camera angle and the rotations of the glass, table and wood texture of the table. As a final measure we increase the ``RenderingResolutionPercentage`` and the ``CyclesSamples`` to get a high-resolution image as output.

To call the execution we now execute our recipe as we normally do with the addition of the argument ``multirun``

.. code-block:: python

    python run.py --config-dir=recipes --config-name=chocBeans_glassTable --multirun initial_runtime_state.seed="range(10)"

The number in brackets behind ``range`` can be set to the desired number of output images. The images below show some example images of our fully automated series production of chocolate beans, whereas all captures are unique and randomized in various parameters.

.. image:: ../_static/tuts/chocBeans_glassTable/multi_seed3_real.png
    :width: 16.0 %
.. image:: ../_static/tuts/chocBeans_glassTable/multi_seed9_real.png
    :width: 16.0 %
.. image:: ../_static/tuts/chocBeans_glassTable/multi_seed11_real.png
    :width: 16.0 %
.. image:: ../_static/tuts/chocBeans_glassTable/multi_seed13_real.png
    :width: 16.0 %
.. image:: ../_static/tuts/chocBeans_glassTable/multi_seed19_real.png
    :width: 16.0 %
.. image:: ../_static/tuts/chocBeans_glassTable/multi_seed20_real.png
    :width: 16.0 %
.. image:: ../_static/tuts/chocBeans_glassTable/multi_seed3_cat.png
    :width: 16.0 %
.. image:: ../_static/tuts/chocBeans_glassTable/multi_seed9_cat.png
    :width: 16.0 %
.. image:: ../_static/tuts/chocBeans_glassTable/multi_seed11_cat.png
    :width: 16.0 %
.. image:: ../_static/tuts/chocBeans_glassTable/multi_seed13_cat.png
    :width: 16.0 %
.. image:: ../_static/tuts/chocBeans_glassTable/multi_seed19_cat.png
    :width: 16.0 %
.. image:: ../_static/tuts/chocBeans_glassTable/multi_seed20_cat.png
    :width: 16.0 %
.. image:: ../_static/tuts/chocBeans_glassTable/multi_seed3_pink.png
    :width: 16.0 %
.. image:: ../_static/tuts/chocBeans_glassTable/multi_seed9_pink.png
    :width: 16.0 %
.. image:: ../_static/tuts/chocBeans_glassTable/multi_seed11_pink.png
    :width: 16.0 %
.. image:: ../_static/tuts/chocBeans_glassTable/multi_seed13_pink.png
    :width: 16.0 %
.. image:: ../_static/tuts/chocBeans_glassTable/multi_seed19_pink.png
    :width: 16.0 %
.. image:: ../_static/tuts/chocBeans_glassTable/multi_seed20_pink.png
    :width: 16.0 %
